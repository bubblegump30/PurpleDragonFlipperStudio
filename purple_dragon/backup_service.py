"""Verified directory backups and previewed restore into a new SD folder only."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import time
import tempfile
import uuid
from .sd_protocol import LIMIT, StorageError, child_path, sd_path

MAX_ENTRIES = 2000
MAX_TOTAL = 256 * 1024 * 1024
MAX_MANIFEST = 2 * 1024 * 1024


def relative_path(value):
    if not isinstance(value, str) or not value or value.startswith('/'):
        raise StorageError('Invalid relative backup path.')
    current = '/ext'
    for component in value.split('/'):
        current = child_path(current, component)
    return value


def verified_payload(folder, entry):
    folder = Path(folder)
    payload = folder / entry['object']
    if folder.is_symlink() or (folder / 'data').is_symlink() or payload.is_symlink() or not payload.is_file():
        raise StorageError('Invalid or linked backup payload.')
    with payload.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    if len(data) != entry['size'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise StorageError('Backup checksum or size mismatch: ' + entry['path'])
    return data


def read_backup(folder, allow_incomplete=False):
    folder = Path(folder)
    if folder.name.casefold().endswith('.incomplete') and not allow_incomplete:
        raise StorageError('Incomplete backups cannot be restored.')
    manifest_file = folder / 'manifest.json'
    if folder.is_symlink() or manifest_file.is_symlink() or not manifest_file.is_file() or manifest_file.stat().st_size > MAX_MANIFEST:
        raise StorageError('Select a complete backup folder with a valid manifest.json.')
    with manifest_file.open('rb') as stream:
        raw = stream.read(MAX_MANIFEST + 1)
    if len(raw) > MAX_MANIFEST: raise StorageError('Backup manifest exceeds its size limit.')
    manifest = json.loads(raw)
    if not isinstance(manifest, dict) or manifest.get('format') != 'purple-dragon-sd-backup' or type(manifest.get('schema')) is not int or manifest['schema'] != 1 or manifest.get('complete') is not True:
        raise StorageError('Unsupported or incomplete backup.')
    sd_path(manifest.get('source'))
    files, directories = manifest.get('files'), manifest.get('directories')
    if not isinstance(files, list) or not isinstance(directories, list) or len(files) + len(directories) > MAX_ENTRIES:
        raise StorageError('Backup exceeds entry limits.')
    seen = {}; directory_names = set(); total = 0
    for directory in directories:
        relative_path(directory)
        key = directory.casefold()
        if key in seen: raise StorageError('Duplicate backup paths.')
        seen[key] = 'directory'; directory_names.add(key)
    objects = set()
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {'path', 'size', 'sha256', 'object'}:
            raise StorageError('Invalid backup file entry.')
        relative_path(entry['path'])
        key = entry['path'].casefold()
        if key in seen: raise StorageError('Duplicate or conflicting backup paths.')
        seen[key] = 'file'
        if type(entry['size']) is not int or not 0 <= entry['size'] <= LIMIT:
            raise StorageError('Backup file exceeds the 4 MiB limit.')
        if not isinstance(entry['sha256'], str) or len(entry['sha256']) != 64 or any(c not in '0123456789abcdef' for c in entry['sha256']):
            raise StorageError('Invalid backup checksum.')
        obj = entry['object']
        if not isinstance(obj, str) or len(obj) != 15 or not obj.startswith('data/') or not obj[5:11].isdigit() or not obj.endswith('.bin') or obj in objects:
            raise StorageError('Invalid backup object reference.')
        objects.add(obj)
        verified_payload(folder, entry)
        total += entry['size']
        if total > MAX_TOTAL: raise StorageError('Backup exceeds the 256 MiB total limit.')
    for key in seen:
        parent = str(PurePosixPath(key).parent)
        if parent != '.' and parent not in directory_names:
            raise StorageError('Backup omits a parent directory.')
    return manifest, hashlib.sha256(raw).hexdigest(), total


class BackupService:
    def __init__(self, client):
        self.client = client

    def check(self):
        self.client.check(self.client.overall)

    def scan(self, source):
        sd_path(source)
        queue = [(source, '')]; directories = []; files = []; total = 0
        while queue:
            self.check()
            remote, relative = queue.pop(0)
            for entry in self.client.listing(remote):
                path = child_path(remote, entry['name'])
                local = entry['name'] if not relative else relative + '/' + entry['name']
                relative_path(local)
                if entry['directory']:
                    directories.append(local); queue.append((path, local))
                else:
                    if entry['size'] > LIMIT: raise StorageError('Backup stopped before download: file exceeds 4 MiB: ' + path)
                    total += entry['size']
                    if total > MAX_TOTAL: raise StorageError('Backup exceeds the 256 MiB total limit.')
                    files.append({'path': local, 'remote': path, 'size': entry['size']})
                if len(files) + len(directories) > MAX_ENTRIES:
                    raise StorageError('Backup exceeds the 2,000 entry limit.')
        return directories, files, total

    def backup(self, source, parent):
        parent = Path(parent)
        if not parent.is_dir(): raise StorageError('Choose an existing backup destination folder.')
        # A backup has a 30-minute overall deadline; each CLI command keeps its own deadline.
        self.client.overall = time.monotonic() + 1800
        directories, files, total = self.scan(source)
        if shutil.disk_usage(parent).free < total + MAX_MANIFEST:
            raise StorageError('Not enough free space for the backup.')
        name = 'PurpleDragon-SD-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
        stage = parent / (name + '.incomplete')
        stage.mkdir(); (stage / 'data').mkdir()
        manifest = {'format':'purple-dragon-sd-backup','schema':1,'complete':True,'source':source,
                    'created_at':datetime.now(timezone.utc).isoformat(),'directories':directories,'files':[]}
        original_progress = self.client.progress; done = 0
        try:
            for index, entry in enumerate(files):
                self.check()
                self.client.progress = lambda current, size, base=done: original_progress(base + current, total)
                obj = 'data/' + str(index).zfill(6) + '.bin'
                result = self.client.download(entry['remote'], stage / obj)
                if result['bytes'] != entry['size']: raise StorageError('Source file changed size during backup.')
                manifest['files'].append({'path':entry['path'],'size':result['bytes'],'sha256':result['sha256'],'object':obj})
                done += result['bytes']; original_progress(done, total)
            self.check()
            with (stage / 'manifest.json').open('w', encoding='utf-8', newline='') as output:
                json.dump(manifest, output, indent=2); output.write('\n'); output.flush(); os.fsync(output.fileno())
            read_backup(stage, allow_incomplete=True)  # Re-read and hash all payloads before publishing the backup.
            self.check()
            final = parent / name
            stage.rename(final)
            return {'folder':str(final),'files':len(files),'directories':len(directories),'bytes':total}
        except Exception as exc:
            # No valid manifest is left on a failed backup, even if failure follows manifest writing.
            (stage / 'manifest.json').unlink(missing_ok=True)
            raise StorageError(str(exc) + ' Incomplete backup remains at ' + str(stage) + '.') from exc
        finally:
            self.client.progress = original_progress

    def preview(self, folder, target):
        # A restore always uses a new direct child of /ext; never merge into existing data.
        if str(PurePosixPath(target).parent) != '/ext':
            raise StorageError('Restore target must be a new folder directly under /ext.')
        sd_path(target, False)
        manifest, digest, total = read_backup(folder)
        for path in manifest['directories'] + [x['path'] for x in manifest['files']]:
            sd_path(target + '/' + path, False)
        if any(e['name'].casefold() == PurePosixPath(target).name.casefold() for e in self.client.listing('/ext')):
            raise StorageError('Restore target already exists. Choose a new folder name.')
        return {'folder':str(folder),'target':target,'manifest_digest':digest,'files':len(manifest['files']),
                'directories':len(manifest['directories']),'bytes':total,
                'paths':[target + '/' + x['path'] for x in manifest['files']],
                'directory_paths':[target + '/' + x for x in manifest['directories']]}

    def restore(self, request):
        self.client.overall = time.monotonic() + 1800
        plan = self.preview(request['folder'], request['target'])
        if plan['manifest_digest'] != request['manifest_digest']:
            raise StorageError('Backup manifest changed after preview. Preview it again before restoring.')
        manifest, digest, _ = read_backup(request['folder'])
        if digest != request['manifest_digest']:
            raise StorageError('Backup manifest changed after preview.')
        root = request['target']; created = False; original_progress = self.client.progress; done = 0
        try:
            self.check()
            self.client.checked(self.client.command('mkdir', root)); created = True
            for relative in sorted(manifest['directories'], key=lambda p: (p.count('/'), p)):
                self.check()
                self.client.checked(self.client.command('mkdir', root + '/' + relative))
            for entry in manifest['files']:
                self.check()
                data = verified_payload(request['folder'], entry)
                self.client.progress = lambda current, size, base=done: original_progress(base + current, plan['bytes'])
                # Upload a private immutable snapshot of the validated local payload.
                with tempfile.TemporaryDirectory(prefix='pd-restore-') as temporary:
                    payload = Path(temporary) / 'payload.bin'
                    payload.write_bytes(data)
                    result = self.client.upload(payload, root + '/' + entry['path'])
                if result['sha256'] != entry['sha256']: raise StorageError('Backup source changed during upload.')
                done += result['bytes']; original_progress(done, plan['bytes'])
            return {'target':root,'files':plan['files'],'directories':plan['directories'],'bytes':plan['bytes']}
        except Exception as exc:
            suffix = ' Partial restore may remain at ' + root + '. No existing files were overwritten.' if created else ''
            raise StorageError(str(exc) + suffix) from exc
        finally:
            self.client.progress = original_progress
