import json
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog,QMessageBox
from purple_dragon.data_io import load_json,read_text,setting_int
from purple_dragon.sd_protocol import StorageClient,StorageError
from purple_dragon.backup_service import read_backup
import test_backup_center as backup_tests
import test_navigation_memory as navigation

class InputAuditTests(unittest.TestCase):
    def test_duplicate_and_nonfinite_json_rejected(self):
        for text in ['{"x":1,"x":2}','[NaN]','[Infinity]','[-Infinity]','[1e999]','['+'1'*1000+']']:
            with self.subTest(text=text),self.assertRaises(ValueError):load_json(text)
    def test_excessive_nesting_and_surrogates_become_validation_errors(self):
        for text in ['['*1100+'0'+']'*1100,'['*34+'0'+']'*34,'"\\ud800"']:
            with self.assertRaises(ValueError):load_json(text)
    def test_size_bound_and_bom_file_read(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'data';path.write_bytes(b'\xef\xbb\xbf{}')
            self.assertEqual(load_json(read_text(path,5)),{})
            with self.assertRaises(ValueError):read_text(path,4)
        with self.assertRaises(ValueError):load_json('[]',1)
    def test_setting_integer_fallback_and_range(self):
        settings=Mock();settings.value.return_value='bad';self.assertEqual(setting_int(settings,'x',50,5,90),50)
        settings.value.return_value=999;self.assertEqual(setting_int(settings,'x',50,5,90),90)

class StorageAuditTests(unittest.TestCase):
    def test_zero_negative_or_invalid_serial_write_fails(self):
        for value in [0,-1,True,None,5000]:
            stream=Mock();stream.write.return_value=value
            with self.subTest(value=value),self.assertRaises(StorageError):StorageClient(stream).write(b'abc')
    def test_partial_serial_write_completes_without_dropping_bytes(self):
        stream=Mock();sent=[]
        def write(data):sent.append(data[:1]);return 1
        stream.write.side_effect=write;StorageClient(stream).write(b'abc')
        self.assertEqual(b''.join(sent),b'abc')
    def test_unknown_mutation_reply_is_not_success(self):
        client=StorageClient(Mock())
        with patch.object(client,'header'),patch.object(client,'finish',return_value=b'Unknown command\r\n'):
            for operation in ['mkdir','remove','copy']:
                with self.assertRaises(StorageError):client.command(operation,'/ext/new')
    def test_cancelled_download_preserves_existing_destination(self):
        from test_sd_manager import FakeStorage
        import tempfile
        stream=FakeStorage();cancelled=[False];client=StorageClient(stream,cancelled=lambda:cancelled[0]);md5=client.md5
        def stop(remote):digest=md5(remote);cancelled[0]=True;return digest
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'existing';target.write_bytes(b'original')
            with patch.object(client,'md5',side_effect=stop),self.assertRaises(StorageError):client.download('/ext/binary.bin',target)
            self.assertEqual(target.read_bytes(),b'original')

    def test_cancel_mid_console_write_does_not_report_a_transport_fault(self):
        from purple_dragon.backend import SerialSession
        worker=SerialSession('test',115200);worker.send('abc');faults=[];worker.fault.connect(faults.append)
        stream=Mock(in_waiting=0)
        def write(data):worker.requestInterruption();return 1
        stream.write.side_effect=write;context=Mock();context.__enter__=Mock(return_value=stream);context.__exit__=Mock(return_value=False)
        with patch('purple_dragon.backend.serial.Serial',return_value=context):worker.run()
        self.assertEqual(faults,[]);self.assertFalse(worker.send('after shutdown'))

class BackupAuditTests(unittest.TestCase):
    setUp=backup_tests.BackupServiceTests.setUp
    make_backup=backup_tests.BackupServiceTests.make_backup
    def test_cancel_during_local_validation_prevents_restore_writes(self):
        result=self.make_backup();before=list(self.stream.commands);calls=[0]
        def check():
            calls[0]+=1
            if calls[0]>=3:raise StorageError('cancelled during verification')
        with patch.object(self.service,'check',side_effect=check),self.assertRaisesRegex(StorageError,'cancelled'):
            self.service.preview(result['folder'],'/ext/new')
        self.assertEqual(self.stream.commands,before);self.assertNotIn('/ext/new',self.stream.dirs)
    def test_duplicate_manifest_fields_rejected(self):
        result=self.make_backup();path=Path(result['folder'])/'manifest.json';text=path.read_text();path.write_text(text.replace('"schema": 1','"schema": 1, "schema": 1'))
        with self.assertRaisesRegex(ValueError,'Duplicate'):read_backup(result['folder'])

class UIAuditTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_corrupt_store_is_preserved_for_every_preset_mutation_and_export(self):
        self.w.profile_name.setText('Saved');self.w.save_profile();self.w.settings.setValue('profiles','{broken')
        with patch.object(self.w,'notify') as notice,patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes),patch.object(self.w,'export_text') as export:
            for method in [self.w.delete_profile,self.w.rename_profile,self.w.duplicate_profile,self.w.export_profiles]:method()
            self.assertEqual(notice.call_count,4);export.assert_not_called()
        self.assertEqual(self.w.settings.value('profiles'),'{broken')
    def test_nested_corrupt_stores_do_not_crash_startup(self):
        self.w.close();deep='['*1100+'0'+']'*1100
        for key in ['profiles','ir_libraries','command_favorites']:self.settings.setValue(key,deep)
        self.settings.setValue('window_geometry','not geometry');self.settings.setValue('speed','not a number')
        self.w=self.create_window();self.assertFalse(self.w.geometry_restored)
        for key in ['profiles','ir_libraries','command_favorites']:self.assertEqual(self.settings.value(key),deep)
    def test_duplicate_import_and_invalid_unicode_export_report_failure(self):
        path=Path(self.temp.name)/'bad.json';path.write_text('{"x":1,"x":2}')
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')),patch.object(self.w,'notify') as notice:
            self.w.import_profiles();self.assertEqual(notice.call_args.args[0],'Import failed')
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(Path(self.temp.name)/'text'),'')),patch.object(self.w,'notify') as notice:
            self.w.export_text('\ud800','Export','text','Text');self.assertEqual(notice.call_args.args[0],'Export failed')
    def test_profile_unknown_fields_do_not_persist_unvalidated_data(self):
        with self.assertRaises(ValueError):self.w.validate_profiles({'name':{'pin':'PA7','notes':'','extra':{'unknown':True}}})
    def test_local_labels_render_untrusted_text_literally(self):
        from purple_dragon.base_window import label
        widget=label('<b>literal</b>');self.assertEqual(widget.textFormat(),Qt.TextFormat.PlainText)
    def test_ir_session_reset_removes_capability(self):
        self.w.device_adapter.capabilities|={'ir_tx'};self.w.reset_ir_session();self.assertNotIn('ir_tx',self.w.device_adapter.capabilities)
    def test_busy_backup_clears_old_preview_even_if_queue_rejects(self):
        from test_device_protocol import INFO
        worker=Mock();worker.request_storage.return_value=False;self.w.session=worker;self.w.connected=True
        self.w.device_adapter.complete({'ok':True,'response':INFO});self.w.sd_available=True;self.w.backup_preview.setPlainText('stale preview')
        self.w.start_backup_job('backup','/ext','destination');self.assertEqual(self.w.backup_preview.toPlainText(),'');self.assertFalse(self.w.sd_busy)
        self.w.session=None;self.w.connected=False

    def test_close_wait_disables_device_controls_before_worker_finishes(self):
        from PySide6.QtGui import QCloseEvent
        from test_device_protocol import INFO
        worker=Mock();worker.wait.return_value=False;self.w.session=worker;self.w.connected=True
        self.w.device_adapter.complete({'ok':True,'response':INFO});self.w.update_sd_controls()
        event=QCloseEvent();self.w.closeEvent(event)
        self.assertFalse(event.isAccepted());self.assertFalse(self.w.send_btn.isEnabled());self.assertFalse(self.w.device_adapter.capabilities)
        self.assertTrue(self.w.connection_cancelled);self.w.session=None;self.w.connected=False
    def test_reconnect_clears_prior_workspace_errors(self):
        self.w.port.addItem('test','COM3');self.w.port.setCurrentIndex(self.w.port.findData('COM3'))
        self.w.session=Mock();self.w.sd_last_error=self.w.backup_last_error=self.w.ir_last_error='old workspace failure'
        self.w.serial_opened()
        self.assertNotIn('old workspace failure',self.w.sd_status.text()+self.w.ir_status.text()+self.w.backup_status.text())
        self.w.session=None;self.w.connected=False

    def test_long_saved_names_do_not_force_horizontal_page_overflow(self):
        from test_ir_qol import TEXT
        self.w.close();self.settings.setValue('profiles',json.dumps({'P'*120:{'pin':'PA7 (pin 2)','notes':'notes'}}))
        self.settings.setValue('ir_libraries',json.dumps([{'title':'L'*80,'text':TEXT.replace('Power','S'*120)}]))
        self.w=self.create_window();self.w.resize(980,760)
        for page in ['GPIO Lab','IR Remote Studio','UART Console']:
            self.w.navigate(page);self.app.processEvents()
            self.assertEqual(self.w.stack.currentWidget().horizontalScrollBar().maximum(),0,page)

    def test_duplicate_cannot_turn_valid_store_into_oversized_store(self):
        data={str(i):{'pin':'PA7 (pin 2)','notes':'x'*100000} for i in range(49)}
        original=json.dumps(data);self.w.settings.setValue('profiles',original);self.w.refresh_profiles('0')
        with patch.object(self.w,'notify') as notice:self.w.duplicate_profile()
        self.assertEqual(notice.call_args.args[0],'Setup could not be duplicated')
        self.assertEqual(self.w.settings.value('profiles'),original)
        self.w.settings.setValue('profiles','{}')
