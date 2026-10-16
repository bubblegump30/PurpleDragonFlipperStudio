import hashlib
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from purple_dragon.sd_protocol import StorageClient, StorageError, sd_path, child_path, parse_listing, LIMIT
from purple_dragon.backend import SerialSession
import test_navigation_memory as navigation
from test_device_protocol import INFO


class FakeStorage:
    """Synthetic CLI emulator; no hardware validation is implied."""
    def __init__(self):
        self.files = {'/ext/binary.bin': b'\x00\xff\x1b[31m\r\n>: \r\nSize: 10\r\n'}
        self.dirs = {'/ext'}
        self.output = b''; self.command_buffer = b''; self.commands = []
        self.pending = None; self.remaining = 0; self.bad_md5 = False; self.race_target = None

    @property
    def in_waiting(self): return len(self.output)

    def read(self, n):
        data, self.output = self.output[:n], self.output[n:]
        return data

    def write(self, data):
        length = len(data)
        if self.pending is not None:
            take = min(len(data), self.remaining)
            self.files[self.pending] += data[:take]; self.remaining -= take
            if self.remaining == 0:
                self.pending = None; self.output += b'\r\n>: '
            return take
        self.command_buffer += data
        if b'\r' not in self.command_buffer: return length
        line, self.command_buffer = self.command_buffer.split(b'\r', 1)
        command = line.decode(); self.commands.append(command)
        args = shlex.split(command); verb, path = args[1:3]
        self.output += b'>: ' + line + b'\r\n'
        body = b''
        if verb == 'list':
            prefix = path + '/'; entries = []
            for folder in sorted(self.dirs):
                if folder.startswith(prefix) and '/' not in folder[len(prefix):]: entries.append('\t[D] ' + folder[len(prefix):])
            for file, content in sorted(self.files.items()):
                if file.startswith(prefix) and '/' not in file[len(prefix):]: entries.append('\t[F] ' + file[len(prefix):] + ' ' + str(len(content)) + 'b')
            body = ('\r\n'.join(entries) if entries else '\tEmpty').encode() + b'\r\n'
        elif verb == 'read':
            content = self.files[path]; body = b'Size: ' + str(len(content)).encode() + b'\r\n' + content + b'\r\n'
        elif verb == 'write_chunk':
            self.files.setdefault(path, b''); self.remaining = int(args[3]); self.pending = path if self.remaining else None
            self.output += b'Ready\r\n'
            if not self.remaining: self.output += b'\r\n>: '
            return length
        elif verb == 'md5':
            body = (('0'*32) if self.bad_md5 else hashlib.md5(self.files[path]).hexdigest()).encode() + b'\r\n'
        elif verb == 'copy':
            target = args[3]
            if target == self.race_target: self.files[target] = b'external existing data'
            if target in self.files: body = b'Storage error: already exists\r\n'
            else: self.files[target] = self.files[path]
        elif verb == 'remove':
            if path in self.files: del self.files[path]
            elif path in self.dirs and not any(x.startswith(path + '/') for x in self.files.keys() | self.dirs): self.dirs.remove(path)
            else: body = b'Storage error: directory not empty\r\n'
        elif verb == 'mkdir': self.dirs.add(path)
        else: raise AssertionError(command)
        self.output += body + b'>: '
        return length


class SDProtocolTests(unittest.TestCase):
    def test_paths_reject_escape_injection_and_root_modification(self):
        for path in ['/int/a', '/ext/../int', '/ext/a/../b', '/ext//a', '/ext/a\rremove', '/ext/a"', '/ext/a\\b']:
            with self.subTest(path=path), self.assertRaises(StorageError): sd_path(path)
        with self.assertRaises(StorageError): sd_path('/ext', False)
        with self.assertRaises(StorageError): child_path('/ext', '../bad')
        self.assertEqual(child_path('/ext', 'file with spaces.bin'), '/ext/file with spaces.bin')

    def test_listing_and_unknown_errors(self):
        self.assertEqual(parse_listing(b'\t[D] folder\r\n\t[F] x y.bin 12b\r\n')[1]['size'], 12)
        self.assertEqual(parse_listing(b'\tEmpty\r\n'), [])
        for body in [b'', b'Storage error: SD card not mounted', b'\t[D] ..', b'\t[F] a 1b\r\n\t[F] A 2b']:
            with self.assertRaises(StorageError): parse_listing(body)

    def test_binary_download_preserves_ansi_prompt_and_null_bytes(self):
        stream = FakeStorage(); progress = []
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'download.bin'
            result = StorageClient(stream, progress=lambda *x: progress.append(x)).download('/ext/binary.bin', target)
            self.assertEqual(target.read_bytes(), stream.files['/ext/binary.bin'])
            self.assertEqual(result['sha256'], hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertTrue(progress)

    def test_failed_download_checksum_preserves_existing_destination(self):
        stream = FakeStorage(); stream.bad_md5 = True
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'keep.bin'; target.write_bytes(b'original')
            with self.assertRaisesRegex(StorageError, 'checksum mismatch'):
                StorageClient(stream).download('/ext/binary.bin', target)
            self.assertEqual(target.read_bytes(), b'original')

    def test_staged_upload_checksums_and_no_rename(self):
        stream = FakeStorage()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'; source.write_bytes(bytes(range(256))*9)
            result = StorageClient(stream).upload(source, '/ext/new file.bin')
            self.assertEqual(stream.files['/ext/new file.bin'], source.read_bytes())
            self.assertEqual(result['bytes'], 2304)
            self.assertFalse(any('.part' in name for name in stream.files))
            self.assertFalse(any('rename' in command for command in stream.commands))
            with self.assertRaisesRegex(StorageError, 'destination exists'):
                StorageClient(stream).upload(source, '/ext/new file.bin')

    def test_upload_copy_race_does_not_overwrite_and_keeps_stage(self):
        stream = FakeStorage(); stream.race_target = '/ext/race.bin'
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'; source.write_bytes(b'new bytes')
            client = StorageClient(stream)
            with self.assertRaises(StorageError): client.upload(source, stream.race_target)
            self.assertEqual(stream.files[stream.race_target], b'external existing data')
            self.assertIn(client.staged, stream.files)

    def test_empty_file_upload_and_transfer_limits(self):
        stream = FakeStorage()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'zero'; source.write_bytes(b'')
            StorageClient(stream).upload(source, '/ext/zero.bin')
            self.assertEqual(stream.files['/ext/zero.bin'], b'')
            with source.open('wb') as f: f.truncate(LIMIT+1)
            with self.assertRaises(StorageError): StorageClient(stream).upload(source, '/ext/large.bin')

    def test_cancel_before_write_and_worker_exclusion_release(self):
        stream = FakeStorage()
        with self.assertRaisesRegex(StorageError, 'cancelled'):
            StorageClient(stream, cancelled=lambda: True).listing('/ext')
        self.assertEqual(stream.commands, [])
        navigation.NavigationMemoryTests.setUpClass()
        worker = SerialSession('test', 230400)
        self.assertTrue(worker.request_storage('list', '/ext'))
        self.assertFalse(worker.send('cannot interleave'))
        request = worker.outbox.get_nowait(); result = []
        worker.storage_result.connect(lambda r: result.append((r, worker.query_pending)))
        worker.storage_operation(stream, request)
        self.assertTrue(result[0][0]['ok']); self.assertFalse(result[0][1])

    def test_missing_card_failure_stops_transport(self):
        navigation.NavigationMemoryTests.setUpClass()
        worker = SerialSession('test', 230400); result = []
        worker.storage_result.connect(result.append)
        with patch('purple_dragon.backend.StorageClient.execute', side_effect=StorageError('SD card not mounted')), patch.object(worker, 'requestInterruption') as stop:
            worker.storage_operation(FakeStorage(), {'operation':'list','path':'/ext','local':None})
        stop.assert_called_once(); self.assertFalse(result[0]['ok'])

    def test_timeout_and_nonrecursive_deletion(self):
        stream = Mock(in_waiting=0); stream.write.side_effect = len; stream.read.return_value = b''
        with patch('purple_dragon.sd_protocol.time.monotonic', side_effect=iter(range(100))):
            with self.assertRaisesRegex(StorageError, 'timed out'): StorageClient(stream).listing('/ext')
        stream = FakeStorage(); stream.dirs.add('/ext/folder'); stream.files['/ext/folder/keep'] = b'keep'
        with self.assertRaises(StorageError): StorageClient(stream).execute('remove','/ext/folder')
        self.assertIn('/ext/folder/keep', stream.files)
        count = len(stream.commands)
        with self.assertRaises(StorageError): StorageClient(stream).execute('remove','/ext')
        self.assertEqual(len(stream.commands),count)

    def test_fragmented_binary_download_and_atomic_replace_failure(self):
        stream = FakeStorage(); original_read = stream.read
        stream.read = lambda n: original_read(min(n,3))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'keep'; target.write_bytes(b'original')
            with patch('purple_dragon.sd_protocol.os.replace', side_effect=OSError('replacement failed')):
                with self.assertRaises(OSError): StorageClient(stream).download('/ext/binary.bin', target)
            self.assertEqual(target.read_bytes(),b'original')
            self.assertEqual(list(Path(tmp).iterdir()),[target])
            StorageClient(stream).download('/ext/binary.bin',target)
            self.assertEqual(target.read_bytes(), stream.files['/ext/binary.bin'])

    def test_remote_download_size_limit_preserves_destination(self):
        stream = FakeStorage(); stream.files['/ext/large'] = b'x' * (LIMIT+1)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'keep'; target.write_bytes(b'original')
            with self.assertRaisesRegex(StorageError,'4 MiB'): StorageClient(stream).download('/ext/large',target)
            self.assertEqual(target.read_bytes(),b'original')


class SDManagerTests(unittest.TestCase):
    setUpClass = classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp = navigation.NavigationMemoryTests.setUp
    create_window = navigation.NavigationMemoryTests.create_window
    tearDown = navigation.NavigationMemoryTests.tearDown

    def ready(self):
        self.worker = Mock(); self.worker.request_storage.return_value = True
        self.w.session = self.worker; self.w.connected = True; self.w.mode.setCurrentText('CLI')
        self.w.device_adapter.complete({'ok':True,'response':INFO}); self.w.update_sd_controls()
        self.addCleanup(self.clear_session)

    def clear_session(self): self.w.session = None; self.w.connected = False

    def probe(self):
        self.w.start_sd_operation('list', '/ext')
        self.w.sd_operation_finished(self.worker, {'ok':True,'operation':'list','path':'/ext','entries':[{'name':'data.bin','directory':False,'size':10}]})
        self.w.sd_tree.setCurrentItem(self.w.sd_tree.topLevelItem(0))

    def test_gate_until_identity_and_successful_sd_probe(self):
        self.assertFalse(self.w.sd_refresh_btn.isEnabled())
        self.ready(); self.assertTrue(self.w.sd_refresh_btn.isEnabled())
        self.assertFalse(self.w.sd_upload_btn.isEnabled()); self.probe()
        self.assertTrue(self.w.sd_download_btn.isEnabled())
        self.assertIn('sd_files', self.w.device_adapter.capabilities)

    def test_delete_requires_confirmation_and_worker_never_removes_root(self):
        self.ready(); self.probe(); self.worker.reset_mock()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No): self.w.sd_delete()
        self.worker.request_storage.assert_not_called()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes): self.w.sd_delete()
        self.worker.request_storage.assert_called_once_with('remove','/ext/data.bin',None)

    def test_disconnect_clears_stale_entries_and_late_results(self):
        self.ready(); self.probe(); self.w.start_sd_operation('list','/ext')
        self.w.connection_lost = True; self.w.serial_finished()
        self.w.sd_operation_finished(self.worker, {'ok':True,'operation':'list','path':'/ext','entries':[]})
        self.assertEqual(self.w.sd_tree.topLevelItemCount(),0)
        self.assertFalse(self.w.sd_available); self.assertFalse(self.w.sd_delete_btn.isEnabled())

    def test_transfer_blocks_identity_and_console_and_cancel_disconnects(self):
        self.ready(); self.probe(); self.w.start_sd_operation('download','/ext/data.bin','local')
        self.w.command.setText('must not send'); self.w.send_command(); self.w.identify_device()
        self.worker.send.assert_not_called(); self.worker.request_device_info.assert_not_called()
        with patch.object(self.w, 'toggle_connection') as close: self.w.sd_cancel()
        close.assert_called_once()
