import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QMessageBox
from purple_dragon.sd_protocol import StorageClient, StorageError
from purple_dragon.gpio_protocol import PINS
from test_device_protocol import INFO
import test_navigation_memory as navigation

USAGE=b'Usage:\r\ngpio <cmd> <args>\r\nmode <pin_name> <0|1> - Set gpio mode: 0 - input, 1 - output\r\nset <pin_name> <0|1>\r\nread <pin_name>\r\n'
class GPIOStream:
    def __init__(self):self.output=b'';self.commands=[];self.bad=None
    @property
    def in_waiting(self):return len(self.output)
    def read(self,n):data,self.output=self.output[:n],self.output[n:];return data
    def write(self,data):
        command=data.rstrip(b'\r').decode();self.commands.append(command)
        if command=='gpio':body=USAGE
        else:
            _,action,pin,*value=command.split()
            if action=='mode':body=('Pin '+pin+(' is now an input' if value==['0'] else ' is now an output (low)')).encode()
            elif action=='read':body=('Pin '+pin+' <= 1').encode()
            else:body=('Pin '+pin+' => '+value[0]).encode()
        self.output+=b'>: '+command.encode()+b'\r\n'+(self.bad if self.bad is not None else body)+b'\r\n>: '
        return len(data)

class GPIOProtocolTests(unittest.TestCase):
    def setUp(self):self.stream=GPIOStream();self.client=StorageClient(self.stream)
    def execute(self,action,pin='PA7'):return self.client.execute('gpio_action','/ext',{'pin':pin,'action':action})
    def probe(self):return self.client.execute('gpio_probe','/ext')
    def test_probe_is_explicit_read_only(self):
        self.assertTrue(self.probe()['supported']);self.assertEqual(self.stream.commands,['gpio'])
        self.assertEqual(self.client.gpio_state['modes'],{})
    def test_unprobed_and_unsupported_pins_never_write(self):
        with self.assertRaises(StorageError):self.execute('Input')
        self.probe();before=list(self.stream.commands)
        for pin in ['PA13','PB6','PB8','PB14','5V','PA7; reboot',None]:
            with self.subTest(pin=pin),self.assertRaises(StorageError):self.execute('Output',pin)
        self.assertEqual(self.stream.commands,before)
    def test_all_regular_pins_input_read_output_low_high(self):
        self.probe()
        for pin in PINS:
            self.execute('Input',pin);self.assertEqual(self.execute('Read',pin)['value'],1)
            self.assertEqual(self.execute('Output',pin)['value'],0)
            self.assertEqual(self.execute('HIGH',pin)['value'],1);self.assertEqual(self.execute('LOW',pin)['value'],0)
        self.assertIn('gpio mode PA7 0',self.stream.commands);self.assertIn('gpio mode PA7 1',self.stream.commands)
    def test_mode_preconditions_checked_in_worker(self):
        self.probe()
        for action in ['Read','LOW','HIGH']:
            with self.assertRaises(StorageError):self.execute(action)
        self.execute('Input')
        with self.assertRaises(StorageError):self.execute('HIGH')
        self.execute('Output')
        with self.assertRaises(StorageError):self.execute('Read')
    def test_strict_response_and_wrong_pin_rejected(self):
        self.probe()
        for body in [b'Err: pin PA7 is busy.',b'Pin PA6 is now an input',b'Pin PA7 is now an input\r\nextra']:
            self.stream.bad=body
            with self.assertRaises(StorageError):self.execute('Input')
            self.assertNotIn('PA7',self.client.gpio_state['modes'])
    def test_reprobe_clears_modes_and_bad_usage_refused(self):
        self.probe();self.execute('Output');self.probe()
        with self.assertRaises(StorageError):self.execute('HIGH')
        self.stream.bad=b'Unknown command'
        with self.assertRaises(StorageError):self.probe()
        self.assertEqual(self.client.gpio_state,{})
    def test_cancellation_sends_nothing(self):
        self.client.cancelled=lambda:True
        with self.assertRaises(StorageError):self.probe()
        self.assertEqual(self.stream.commands,[])
    def test_worker_keeps_state_between_jobs_and_identity_refresh_invalidates(self):
        from purple_dragon.backend import SerialSession
        worker=SerialSession('test',115200)
        worker.storage_operation(self.stream,{'operation':'gpio_probe','path':'/ext','local':None})
        worker.storage_operation(self.stream,{'operation':'gpio_action','path':'/ext','local':{'pin':'PA7','action':'Input'}})
        self.assertEqual(worker.gpio_state['modes'],{'PA7':'Input'})
        # Device information refresh clears backend tracking before issuing its command.
        worker.query_device_info(Mock(in_waiting=0,read=Mock(return_value=b'')),Mock(),timeout=0)
        self.assertEqual(worker.gpio_state,{})

class GPIOWorkbenchTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def ready(self):
        self.worker=Mock();self.worker.request_storage.return_value=True
        self.w.session=self.worker;self.w.connected=True;self.w.mode.setCurrentText('CLI')
        self.w.device_adapter.complete({'ok':True,'response':INFO});self.w.update_sd_controls();self.addCleanup(self.clear)
    def clear(self):self.w.session=None;self.w.connected=False
    def probe(self):
        self.w.start_gpio_operation('gpio_probe');self.w.sd_operation_finished(self.worker,{'operation':'gpio_probe','ok':True})
    def finish(self,action,value=None):
        self.w.sd_operation_finished(self.worker,{'operation':'gpio_action','ok':True,'pin':'PA7','action':action,'value':value,'response':'test '+action})
    def test_unidentified_uart_and_busy_gates(self):
        self.assertFalse(self.w.gpio_probe_btn.isEnabled());self.ready()
        self.w.mode.setCurrentText('UART Bridge');self.w.start_gpio_operation('gpio_probe');self.worker.request_storage.assert_not_called()
        self.w.mode.setCurrentText('CLI');self.w.sd_busy=True;self.w.start_gpio_operation('gpio_probe');self.worker.request_storage.assert_not_called()
    def test_output_confirmation_and_arm_required(self):
        self.ready();self.probe();self.assertFalse(self.w.gpio_buttons['HIGH'].isEnabled());self.worker.reset_mock()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No):self.w.gpio_action('Output')
        self.worker.request_storage.assert_not_called()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):self.w.gpio_action('Output')
        self.worker.request_storage.assert_called_once_with('gpio_action','/ext',{'pin':'PA7','action':'Output'})
        self.assertFalse(self.w.send_btn.isEnabled());self.finish('Output',0)
        self.assertTrue(self.w.arm.isEnabled());self.assertFalse(self.w.gpio_buttons['HIGH'].isEnabled())
        self.w.arm.setChecked(True);self.assertTrue(self.w.gpio_buttons['HIGH'].isEnabled())
        self.w.gpio_action('HIGH');self.finish('HIGH',1);self.assertEqual(self.w.gpio_state_value.text(),'HIGH (1)')
        self.w.pin.setCurrentIndex(1);self.assertFalse(self.w.arm.isChecked());self.assertFalse(self.w.gpio_buttons['HIGH'].isEnabled())
    def test_poll_input_only_skip_busy_and_stop_on_navigation(self):
        self.ready();self.probe();self.w.gpio_action('Input');self.finish('Input')
        self.w.poll.setChecked(True);self.assertTrue(self.w.gpio_timer.isActive());self.worker.reset_mock()
        self.w.sd_busy=True;self.w.gpio_poll_tick();self.worker.request_storage.assert_not_called()
        self.w.sd_busy=False;self.w.gpio_poll_tick();self.worker.request_storage.assert_called_once();self.finish('Read',1)
        self.w.navigate('IR Remote Studio');self.assertFalse(self.w.poll.isChecked());self.assertFalse(self.w.gpio_timer.isActive())
    def test_console_send_invalidates_without_gpio_commands(self):
        self.ready();self.probe();self.w.gpio_action('Input');self.finish('Input');self.worker.reset_mock()
        self.w.command.setText('help');self.w.send_command()
        self.assertFalse(self.w.gpio_supported);self.assertEqual(self.w.gpio_states,{});self.worker.request_storage.assert_not_called()
    def test_disconnect_and_stale_results_do_not_restore_state(self):
        self.ready();self.probe();self.w.gpio_action('Input');self.w.connection_lost=True;self.w.serial_finished();self.finish('Input')
        self.assertFalse(self.w.gpio_supported);self.assertEqual(self.w.gpio_states,{})
        self.assertIn('may remain',self.w.gpio_status.text());self.assertFalse(self.w.gpio_timer.isActive())
    def test_error_clears_modes_arm_poll_and_controls(self):
        self.ready();self.probe();self.w.gpio_action('Input');self.finish('Input');self.w.poll.setChecked(True);self.w.gpio_poll_tick()
        self.w.sd_operation_finished(self.worker,{'operation':'gpio_action','ok':False,'error':'timeout'})
        self.assertFalse(self.w.gpio_supported);self.assertFalse(self.w.poll.isChecked());self.assertIn('unknown',self.w.gpio_status.text())
    def test_setups_never_apply_device_mode_and_history_is_bounded(self):
        self.ready();self.probe();self.worker.reset_mock();self.w.profile.setEditText('test');self.w.save_profile();self.w.load_profile()
        self.worker.request_storage.assert_not_called();self.assertFalse(self.w.arm.isChecked())
        self.w.gpio_states['PA7']={'mode':'Output','value':0};self.w.update_gpio_controls();self.w.arm.setChecked(True)
        self.w.load_profile();self.assertFalse(self.w.arm.isChecked())
        self.w.gpio_states['PA7']={'mode':'Input','value':None};self.w.update_gpio_controls();self.w.poll.setChecked(True)
        self.w.close();self.assertFalse(self.w.gpio_timer.isActive())
        for i in range(510):self.w.history.appendPlainText(str(i))
        self.assertEqual(self.w.history.blockCount(),500)
