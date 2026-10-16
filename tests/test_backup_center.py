import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QFileDialog, QMessageBox
from purple_dragon.backup_service import BackupService, read_backup
from purple_dragon.sd_protocol import StorageClient, StorageError, LIMIT
from test_sd_manager import FakeStorage
from test_device_protocol import INFO
import test_navigation_memory as navigation


class BackupServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.stream = FakeStorage()
        self.stream.dirs.update({'/ext/folder','/ext/folder/empty'})
        self.stream.files['/ext/folder/private.bin'] = b'\x00\xffbinary\r\n>: '
        self.client = StorageClient(self.stream)
        self.service = BackupService(self.client)

    def make_backup(self):
        return self.service.backup('/ext',self.parent)

    def test_backup_manifest_payloads_and_empty_directories(self):
        result = self.make_backup(); folder = Path(result['folder'])
        manifest, digest, total = read_backup(folder)
        self.assertEqual(result['files'],2); self.assertEqual(len(digest),64)
        self.assertIn('folder/empty',manifest['directories'])
        self.assertEqual(total,sum(len(data) for data in self.stream.files.values()))
        for entry in manifest['files']:
            self.assertEqual((folder/entry['object']).read_bytes(),self.stream.files['/ext/'+entry['path']])
        self.assertFalse(any(p.name.endswith('.incomplete') for p in self.parent.iterdir()))

    def test_roundtrip_restores_to_new_folder_only(self):
        result = self.make_backup(); original = dict(self.stream.files)
        preview = self.service.preview(result['folder'],'/ext/restored')
        self.assertFalse(any('storage mkdir' in c or 'storage write_chunk' in c for c in self.stream.commands))
        restored = self.service.restore(preview)
        self.assertEqual(restored['files'],2)
        for path,data in original.items():
            self.assertEqual(self.stream.files[path],data)
            self.assertEqual(self.stream.files['/ext/restored/'+path[len('/ext/'):]],data)
        self.assertIn('/ext/restored/folder/empty',self.stream.dirs)

    def test_existing_target_and_unsafe_target_refused(self):
        result = self.make_backup()
        for target in ['/ext/folder','/ext','/int/new','/ext/../new','/ext/nested/new']:
            with self.subTest(target=target), self.assertRaises(StorageError): self.service.preview(result['folder'],target)
        self.assertFalse(any('storage write_chunk' in c for c in self.stream.commands))

    def test_payload_corruption_prevents_restore_writes(self):
        result = self.make_backup(); plan = self.service.preview(result['folder'],'/ext/new')
        manifest,_,_ = read_backup(result['folder'])
        (Path(result['folder'])/manifest['files'][0]['object']).write_bytes(b'changed')
        with self.assertRaises(StorageError): self.service.restore(plan)
        self.assertNotIn('/ext/new',self.stream.dirs)

    def test_manifest_change_after_preview_refused(self):
        result = self.make_backup(); plan = self.service.preview(result['folder'],'/ext/new')
        path = Path(result['folder'])/'manifest.json'; data = json.loads(path.read_text()); data['created_at']='changed'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(StorageError,'changed after preview'): self.service.restore(plan)
        self.assertNotIn('/ext/new',self.stream.dirs)

    def test_manifest_traversal_duplicates_and_incomplete_rejected(self):
        result = self.make_backup(); path=Path(result['folder'])/'manifest.json'; original=json.loads(path.read_text())
        variants=[]
        data=json.loads(json.dumps(original)); data['files'][0]['object']='../outside.bin'; variants.append(data)
        data=json.loads(json.dumps(original)); data['files'][0]['path']='../outside'; variants.append(data)
        data=json.loads(json.dumps(original)); data['files'].append(dict(data['files'][0])); variants.append(data)
        data=json.loads(json.dumps(original)); data['complete']=False; variants.append(data)
        data=json.loads(json.dumps(original)); data['directories']=[]; variants.append(data)
        for variant in variants:
            path.write_text(json.dumps(variant))
            with self.assertRaises(StorageError): read_backup(result['folder'])

    def test_backup_preflight_limits_do_not_publish_or_skip(self):
        self.stream.files['/ext/large.bin']=b'x'*(LIMIT+1)
        with self.assertRaisesRegex(StorageError,'exceeds 4 MiB'): self.make_backup()
        self.assertEqual(list(self.parent.iterdir()),[])
        del self.stream.files['/ext/large.bin']
        with patch('purple_dragon.backup_service.MAX_TOTAL',1):
            with self.assertRaises(StorageError): self.make_backup()
        self.assertEqual(list(self.parent.iterdir()),[])

    def test_cancelled_backup_is_incomplete_and_unrestorable(self):
        cancelled=[False]; self.client.cancelled=lambda:cancelled[0]
        download=self.client.download
        def stop_after_file(*args):
            result=download(*args); cancelled[0]=True; return result
        with patch.object(self.client,'download',side_effect=stop_after_file):
            with self.assertRaisesRegex(StorageError,'Incomplete backup'): self.make_backup()
        stage=list(self.parent.iterdir())[0]
        self.assertTrue(stage.name.endswith('.incomplete'))
        self.assertFalse((stage/'manifest.json').exists())
        with self.assertRaises(StorageError): read_backup(stage)

    def test_failed_restore_reports_partial_new_folder_without_touching_originals(self):
        result=self.make_backup(); plan=self.service.preview(result['folder'],'/ext/partial'); original=dict(self.stream.files)
        with patch.object(self.client,'upload',side_effect=StorageError('transfer failed')):
            with self.assertRaisesRegex(StorageError,'Partial restore may remain'): self.service.restore(plan)
        for path,data in original.items(): self.assertEqual(self.stream.files[path],data)
        self.assertIn('/ext/partial',self.stream.dirs)


class BackupCenterTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown

    def ready(self):
        self.worker=Mock(); self.worker.request_storage.return_value=True
        self.w.session=self.worker; self.w.connected=True; self.w.mode.setCurrentText('CLI')
        self.w.device_adapter.complete({'ok':True,'response':INFO}); self.w.sd_available=True; self.w.update_sd_controls()
        self.addCleanup(self.clear_session)

    def clear_session(self): self.w.session=None; self.w.connected=False

    def plan(self):
        return {'folder':'backup','target':'/ext/restore-new','manifest_digest':'a'*64,'files':1,'directories':0,'bytes':3}

    def test_controls_require_identified_sd_and_preview(self):
        self.assertFalse(self.w.backup_all_btn.isEnabled()); self.ready()
        self.assertTrue(self.w.backup_all_btn.isEnabled()); self.assertFalse(self.w.restore_confirm_btn.isEnabled())
        self.w.backup_plan=self.plan(); self.w.update_sd_controls(); self.assertTrue(self.w.restore_confirm_btn.isEnabled())
        self.w.restore_target.setText('different'); self.assertIsNone(self.w.backup_plan)
        self.assertFalse(self.w.restore_confirm_btn.isEnabled())

    def test_restore_decline_and_accept_uses_exact_preview(self):
        self.ready(); self.w.backup_plan=self.plan(); self.w.update_sd_controls()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No): self.w.confirm_restore()
        self.worker.request_storage.assert_not_called()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes): self.w.confirm_restore()
        self.worker.request_storage.assert_called_once_with('restore','/ext',{'folder':'backup','target':'/ext/restore-new','manifest_digest':'a'*64})
        self.assertTrue(self.w.sd_busy)

    def test_disconnect_invalidates_preview_and_ignores_late_result(self):
        self.ready(); self.w.backup_plan=self.plan(); self.w.update_sd_controls()
        self.w.start_backup_job('restore_preview','/ext',{'folder':'backup','target':'/ext/new'})
        self.w.connection_lost=True; self.w.serial_finished()
        self.w.sd_operation_finished(self.worker,{'operation':'restore_preview','ok':True,**self.plan(),'paths':[],'directory_paths':[]})
        self.assertIsNone(self.w.backup_plan); self.assertFalse(self.w.restore_confirm_btn.isEnabled())
