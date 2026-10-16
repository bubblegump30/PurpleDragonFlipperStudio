import copy
import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
from purple_dragon.ir_files import inspect_ir
from purple_dragon.ir_protocol import signal_command, parse_ir_capabilities, execute_ir
from purple_dragon.sd_protocol import StorageClient, StorageError
from test_ir_qol import TEXT
from test_device_protocol import INFO
import test_navigation_memory as navigation

USAGE=b'Usage:\r\n ir tx <protocol> <address> <command>\r\n Available protocols: NEC NECext Samsung32 SIRC\r\n ir tx RAW F:<frequency> DC:<duty_cycle> <sample0>\r\n'

class IRSerial:
    def __init__(self, body=b''):
        self.output=b''; self.commands=[]; self.body=body
    @property
    def in_waiting(self):return len(self.output)
    def read(self,n):
        data,self.output=self.output[:n],self.output[n:];return data
    def write(self,data):
        command=data.rstrip(b'\r').decode();self.commands.append(command)
        self.output+=b'>: '+command.encode()+b'\r\n'+(USAGE if command=='ir' else self.body)+b'\r\n>: '
        return len(data)


class IRProtocolTests(unittest.TestCase):
    def test_parsed_byte_order_and_protocol_ranges(self):
        entry=inspect_ir(TEXT)[0][0]
        self.assertEqual(signal_command(entry),'ir tx NEC 0 1')
        entry['fields'].update(protocol='NECext',address='34 12 00 00',command='78 56 00 00')
        self.assertEqual(signal_command(entry),'ir tx NECext 1234 5678')
        entry['fields']['address']='00 00 00 01'
        with self.assertRaises(ValueError):signal_command(entry)

    def test_raw_numeric_validation_and_cli_bounds(self):
        raw=inspect_ir(TEXT)[0][1]
        self.assertEqual(signal_command(raw),'ir tx RAW F:38000 DC:33 100 200')
        for key,value in [('frequency','1000001'),('duty_cycle','NaN'),('duty_cycle','0.333333'),('data','0 20'),('data','100; reboot'),('data','1000000 1000000 1'),('data','1 '*513)]:
            bad=copy.deepcopy(raw);bad['fields'][key]=value
            with self.subTest(key=key,value=value[:20]),self.assertRaises(ValueError):signal_command(bad)

    def test_duplicate_fields_names_headers_and_unknown_protocol_block_validation(self):
        for text in [TEXT.replace('protocol: NEC','protocol: NEC\nprotocol: NEC'),TEXT.replace('name: Volume','name: Power'),TEXT.replace('Version: 1','Version: 1\nVersion: 1'),TEXT.replace('protocol: NEC','protocol: Reboot;')]:
            self.assertTrue(inspect_ir(text)[1])

    def test_probe_is_read_only_and_transmit_is_exactly_one_command(self):
        stream=IRSerial();client=StorageClient(stream)
        capabilities=execute_ir(client,'ir_probe',None)
        self.assertEqual(stream.commands,['ir']);self.assertTrue(capabilities['raw'])
        result=execute_ir(client,'ir_transmit',{'entry':inspect_ir(TEXT)[0][0],'capabilities':capabilities})
        self.assertTrue(result['completed']);self.assertEqual(stream.commands,['ir','ir tx NEC 0 1'])

    def test_unadvertised_format_busy_and_device_error_fail(self):
        request={'entry':inspect_ir(TEXT)[0][0],'capabilities':{'protocols':[],'raw':False}}
        stream=IRSerial()
        with self.assertRaises(StorageError):execute_ir(StorageClient(stream),'ir_transmit',request)
        self.assertEqual(stream.commands,[])
        request['capabilities']['protocols']=['NEC']
        with self.assertRaises(StorageError):execute_ir(StorageClient(IRSerial(b'INFRARED is busy. Exiting.')),'ir_transmit',request)
        with self.assertRaises(StorageError):parse_ir_capabilities(b'Unknown command')

    def test_no_cancellation_write(self):
        stream=IRSerial()
        with self.assertRaisesRegex(StorageError,'cancelled'):
            execute_ir(StorageClient(stream,cancelled=lambda:True),'ir_probe',None)
        self.assertEqual(stream.commands,[])


class IRWorkspaceTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown

    def ready(self):
        self.worker=Mock();self.worker.request_storage.return_value=True
        self.w.session=self.worker;self.w.connected=True;self.w.mode.setCurrentText('CLI')
        self.w.device_adapter.complete({'ok':True,'response':INFO});self.w.update_sd_controls()
        self.addCleanup(self.clear_session)

    def clear_session(self):self.w.session=None;self.w.connected=False

    def probe(self):
        self.w.start_ir_operation('ir_probe')
        self.w.sd_operation_finished(self.worker,{'operation':'ir_probe','ok':True,'protocols':['NEC'],'raw':True})

    def test_library_persistence_and_load_without_send(self):
        self.w.load_ir_text(TEXT,'source')
        with patch.object(QInputDialog,'getText',return_value=('Living room',True)):self.w.save_ir_library()
        self.w.close();self.w=self.create_window();self.w.ir_libraries.setCurrentIndex(1)
        self.w.load_ir_library()
        self.assertEqual(self.w.ir_preview.toPlainText(),TEXT)
        self.assertIsNone(self.w.session);self.assertFalse(self.w.ir_transmit_btn.isEnabled())

    def test_library_corruption_preserved_and_duplicates_refused(self):
        self.w.load_ir_text(TEXT,'source');self.w.settings.setValue('ir_libraries','{broken')
        with patch.object(self.w,'notify') as notice:self.w.save_ir_library()
        notice.assert_called_once();self.assertEqual(self.w.settings.value('ir_libraries'),'{broken')
        self.w.settings.setValue('ir_libraries','[]')
        with patch.object(QInputDialog,'getText',return_value=('Room',True)):self.w.save_ir_library()
        with patch.object(QInputDialog,'getText',return_value=('room',True)),patch.object(self.w,'notify'):self.w.save_ir_library()
        self.assertEqual(len(self.w.ir_library_data()),1)

    def test_transmit_gates_probe_and_each_confirmation(self):
        self.ready();self.w.load_ir_text(TEXT,'source');self.assertFalse(self.w.ir_transmit_btn.isEnabled())
        self.probe();self.assertTrue(self.w.ir_transmit_btn.isEnabled());self.worker.reset_mock()
        with patch.object(QMessageBox,'exec',return_value=QMessageBox.StandardButton.No):self.w.confirm_ir_transmit()
        self.worker.request_storage.assert_not_called()
        with patch.object(QMessageBox,'exec',return_value=QMessageBox.StandardButton.Yes):self.w.confirm_ir_transmit()
        self.assertEqual(self.worker.request_storage.call_count,1)
        self.assertEqual(self.worker.request_storage.call_args.args[0],'ir_transmit')
        self.assertTrue(self.w.sd_busy);self.assertFalse(self.w.send_btn.isEnabled())

    def test_storage_job_and_uart_mode_block_ir(self):
        self.ready();self.w.mode.setCurrentText('UART Bridge');self.w.update_sd_controls()
        self.w.start_ir_operation('ir_probe');self.worker.request_storage.assert_not_called()
        self.w.mode.setCurrentText('CLI');self.w.sd_busy=True;self.w.start_ir_operation('ir_probe')
        self.worker.request_storage.assert_not_called()

    def test_disconnect_clears_capabilities_and_late_result(self):
        self.ready();self.probe();self.w.load_ir_text(TEXT,'source');self.assertTrue(self.w.ir_transmit_btn.isEnabled())
        self.w.connection_lost=True;self.w.serial_finished()
        self.w.sd_operation_finished(self.worker,{'operation':'ir_probe','ok':True,'protocols':['NEC'],'raw':True})
        self.assertIsNone(self.w.ir_capabilities);self.assertFalse(self.w.ir_transmit_btn.isEnabled())

    def test_invalid_file_does_not_enable_transmit(self):
        self.ready();self.probe();self.w.load_ir_text(TEXT.replace('command: 01 00 00 00','command: FF FF FF FF'),'invalid')
        self.assertFalse(self.w.ir_transmit_btn.isEnabled());self.assertTrue(self.w.ir_file_warnings)

    def test_library_rename_remove_and_selected_signal_export(self):
        self.w.load_ir_text(TEXT,'source')
        with patch.object(QInputDialog,'getText',return_value=('Room',True)):self.w.save_ir_library()
        self.w.ir_libraries.setCurrentIndex(1)
        with patch.object(QInputDialog,'getText',return_value=('Office',True)):self.w.rename_ir_library()
        self.w.ir_libraries.setCurrentIndex(1);self.assertEqual(self.w.ir_libraries.currentText(),'Office')
        from pathlib import Path
        target=Path(self.temp.name)/'selected.ir'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(target),'Flipper infrared (*.ir)')):self.w.export_ir_signal()
        entries,warnings=inspect_ir(target.read_text())
        self.assertEqual(len(entries),1);self.assertEqual(entries[0]['name'],'Power');self.assertEqual(warnings,[])
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No):self.w.remove_ir_library()
        self.assertEqual(len(self.w.ir_library_data()),1)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):self.w.remove_ir_library()
        self.assertEqual(self.w.ir_library_data(),[]);self.assertEqual(self.w.ir_preview.toPlainText(),TEXT)

    def test_valid_file_can_be_saved_even_when_cli_raw_conversion_is_unsupported(self):
        self.ready();self.probe();self.w.load_ir_text(TEXT.replace('0.33','0.333333'),'valid file')
        self.assertEqual(self.w.ir_file_warnings,[])
        self.w.ir_filter.setText('Volume')
        self.assertFalse(self.w.ir_transmit_btn.isEnabled())
        self.assertIn('percent',self.w.ir_transmit_btn.toolTip())
        with patch.object(QInputDialog,'getText',return_value=('Raw file',True)):self.w.save_ir_library()
        self.assertEqual(len(self.w.ir_library_data()),1)
