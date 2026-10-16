"""Bounded binary-safe CLI storage operations, exclusively owned by SerialSession."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
import uuid

LIMIT = 4 * 1024 * 1024
ANSI = re.compile(rb'\x1b\[[0-?]*[ -/]*[@-~]')
PROMPT = re.compile(rb'(?:^|\r\n)[^\r\n]{0,128}>: $')


class StorageError(ValueError):
    pass


def sd_path(path, allow_root=True):
    if not isinstance(path, str) or len(path.encode('utf-8')) > 512:
        raise StorageError('SD path is too long.')
    if any(ord(c) < 32 or ord(c) == 127 or c in '\\";|<>' for c in path):
        raise StorageError('Unsupported characters in SD path.')
    parts = path.split('/')
    if path != '/ext' and (not path.startswith('/ext/') or any(p in ('', '.', '..') for p in parts[2:])):
        raise StorageError('Only canonical paths inside /ext are allowed.')
    if not allow_root and path == '/ext':
        raise StorageError('The SD root cannot be modified.')
    return path


def child_path(parent, name):
    if not name or '/' in name or name in ('.', '..') or name.endswith((' ', '.')) or len(name.encode('utf-8')) > 255:
        raise StorageError('Enter one valid file or folder name.')
    return sd_path(sd_path(parent) + '/' + name, False)


def parse_listing(body):
    entries = []
    for line in body.decode('utf-8', errors='strict').splitlines():
        if not line.strip() or line.strip() == 'Empty':
            continue
        directory = re.fullmatch(r'\s*\[D\] (.+)', line)
        file = re.fullmatch(r'\s*\[F\] (.+) (\d+)b', line)
        if not directory and not file:
            raise StorageError('Unsupported directory response; no file actions enabled.')
        name = (directory or file).group(1)
        child_path('/ext', name)
        if any(e['name'].casefold() == name.casefold() for e in entries):
            raise StorageError('Ambiguous duplicate directory entries.')
        entries.append({'name': name, 'directory': bool(directory), 'size': None if directory else int(file.group(2))})
        if len(entries) > 2000:
            raise StorageError('Directory exceeds the 2,000 entry limit.')
    if not entries and b'Empty' not in body:
        raise StorageError('Missing directory listing.')
    return entries


class StorageClient:
    def __init__(self, stream, cancelled=lambda: False, progress=lambda *_: None):
        self.stream = stream
        self.cancelled = cancelled
        self.progress = progress
        self.buffer = b''
        self.overall = time.monotonic() + 120
        self.staged = None

    def check(self, deadline):
        if self.cancelled():
            raise StorageError('Operation cancelled; reconnect before using the serial console.')
        if time.monotonic() >= min(deadline, self.overall):
            raise StorageError('Storage response timed out; reconnect to resynchronize the CLI.')

    def write(self, data):
        deadline = time.monotonic() + 10
        while data:
            self.check(deadline)
            written = self.stream.write(data[:1024])
            if not written or written > min(1024, len(data)):
                raise StorageError('Incomplete serial write.')
            data = data[written:]

    def fill(self, deadline):
        self.check(deadline)
        self.buffer += self.stream.read(min(max(self.stream.in_waiting, 1), 4096))
        if len(self.buffer) > LIMIT + 65536:
            raise StorageError('Storage response exceeded its limit.')

    def header(self, command):
        self.write(command.encode('utf-8') + b'\r')
        deadline = time.monotonic() + 10
        while True:
            while b'\r\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\r\n', 1)
                clean = ANSI.sub(b'', line)
                if clean.endswith(command.encode('utf-8')):
                    return
            if len(self.buffer) > 65536:
                raise StorageError('Missing CLI command echo.')
            self.fill(deadline)

    def finish(self):
        deadline = time.monotonic() + 30
        while True:
            clean = ANSI.sub(b'', self.buffer)
            match = PROMPT.search(clean)
            if match:
                self.buffer = b''
                return clean[:match.start()]
            if len(self.buffer) > 65536:
                raise StorageError('CLI response exceeded 64 KiB.')
            self.fill(deadline)

    @staticmethod
    def checked(body):
        if b'Storage error:' in body or b'Usage:' in body or b'Invalid arguments' in body:
            raise StorageError(body.decode('utf-8', errors='replace')[:400].strip())
        return body

    def command(self, verb, path, extra=''):
        sd_path(path)
        self.header('storage ' + verb + ' "' + path + '"' + (' ' + extra if extra else ''))
        return self.finish()

    def listing(self, path):
        return parse_listing(self.checked(self.command('list', path)))

    def md5(self, path):
        body = self.checked(self.command('md5', path)).strip()
        if not re.fullmatch(rb'[0-9a-fA-F]{32}', body):
            raise StorageError('Missing integrity checksum.')
        return body.decode().lower()

    def download(self, remote, local):
        sd_path(remote, False)
        self.header('storage read "' + remote + '"')
        deadline = time.monotonic() + 10
        while b'\r\n' not in self.buffer:
            self.fill(deadline)
        line, self.buffer = self.buffer.split(b'\r\n', 1)
        match = re.fullmatch(rb'Size: (\d+)', line)
        if not match:
            raise StorageError('Missing file-size header; SD file may be unavailable.')
        size = int(match.group(1))
        if size > LIMIT:
            raise StorageError('Files are limited to 4 MiB per transfer.')
        data = bytearray()
        while len(data) < size:
            if not self.buffer:
                self.fill(time.monotonic() + 10)
            take = min(size - len(data), len(self.buffer))
            data.extend(self.buffer[:take]); self.buffer = self.buffer[take:]
            self.progress(len(data), size)
        self.checked(self.finish())
        digest = hashlib.md5(data).hexdigest()
        if self.md5(remote) != digest:
            raise StorageError('Download checksum mismatch; destination was preserved.')
        target = Path(local)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.pd-download-', delete=False) as f:
                temporary = Path(f.name); f.write(data); f.flush(); os.fsync(f.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {'bytes': size, 'sha256': hashlib.sha256(data).hexdigest()}

    def upload(self, local, remote):
        sd_path(remote, False)
        source = Path(local)
        if source.stat().st_size > LIMIT:
            raise StorageError('Files are limited to 4 MiB per transfer.')
        with source.open('rb') as f:
            data = f.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise StorageError('Source grew beyond the transfer limit.')
        parent = str(PurePosixPath(remote).parent)
        if any(e['name'].casefold() == PurePosixPath(remote).name.casefold() for e in self.listing(parent)):
            raise StorageError('Remote destination exists. Choose a different name; overwrite is disabled.')
        stage = child_path(parent, '.pd-upload-' + uuid.uuid4().hex + '.part')
        self.staged = stage
        self.header('storage write_chunk "' + stage + '" ' + str(len(data)))
        deadline = time.monotonic() + 10
        while b'\r\n' not in self.buffer:
            self.fill(deadline)
        ready, self.buffer = self.buffer.split(b'\r\n', 1)
        if ready != b'Ready':
            raise StorageError('Firmware did not accept binary upload.')
        for offset in range(0, len(data), 1024):
            self.write(data[offset:offset+1024]); self.progress(min(offset+1024, len(data)), len(data))
        self.checked(self.finish())
        digest = hashlib.md5(data).hexdigest()
        if self.md5(stage) != digest:
            raise StorageError('Staged upload checksum mismatch.')
        # Firmware copy uses FSOM_CREATE_NEW; rename would remove an existing destination.
        self.checked(self.command('copy', stage, '"' + remote + '"'))
        if self.md5(remote) != digest:
            raise StorageError('Destination checksum mismatch. Inspect the new file and staged upload.')
        self.checked(self.command('remove', stage))
        self.staged = None
        return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def execute(self, operation, path, local=None):
        sd_path(path, operation == 'list')
        if operation == 'list':
            return {'entries': self.listing(path)}
        if operation == 'download':
            return self.download(path, local)
        if operation == 'upload':
            return self.upload(local, path)
        if operation in ('mkdir', 'remove'):
            self.checked(self.command(operation, path))
            return {}
        raise StorageError('Unsupported SD operation.')
