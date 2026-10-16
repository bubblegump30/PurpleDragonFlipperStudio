import codecs
import unittest
from unittest.mock import Mock
from purple_dragon.backend import SerialSession
from purple_dragon.device_protocol import parse_device_info
from test_device_protocol import INFO
import test_navigation_memory as navigation

# Official f7 UID64 is 8 bytes (16 hexadecimal digits); synthetic test data.
UID64_INFO=INFO.replace('0123456789ABCDEF01234567','0123456789ABCDEF')

class IdentityFormatTests(unittest.TestCase):
    def test_official_uid64_and_previous_uid96_are_accepted(self):
        self.assertEqual(parse_device_info(UID64_INFO)['hardware_uid'],'0123456789ABCDEF')
        self.assertEqual(parse_device_info(INFO)['hardware_uid'],'0123456789ABCDEF01234567')
    def test_wrong_length_nonhex_and_wrong_hardware_remain_rejected(self):
        for text in [UID64_INFO.replace('0123456789ABCDEF','0123456789ABCDE'),UID64_INFO.replace('0123456789ABCDEF','0123456789ABCDEF00'),UID64_INFO.replace('0123456789ABCDEF','ZZZZZZZZZZZZZZZZ'),UID64_INFO.replace('hardware_target: 7','hardware_target: 9')]:
            with self.assertRaises(ValueError):parse_device_info(text)
    def test_complete_unsupported_reply_does_not_interrupt_transport(self):
        worker=SerialSession('test',115200);results=[];worker.device_info_result.connect(results.append)
        stream=Mock(in_waiting=0);stream.read.return_value=UID64_INFO.replace('hardware_target: 7','hardware_target: 9').encode()
        worker.query_device_info(stream,codecs.getincrementaldecoder('utf-8')())
        self.assertFalse(results[-1]['ok']);self.assertTrue(results[-1]['recoverable']);self.assertFalse(worker.isInterruptionRequested())
        self.assertTrue(worker.send('help'))
    def test_official_format_chunked_reply_success(self):
        worker=SerialSession('test',115200);results=[];worker.device_info_result.connect(results.append)
        stream=Mock(in_waiting=0);stream.read.side_effect=[UID64_INFO[:45].encode(),UID64_INFO[45:200].encode(),UID64_INFO[200:].encode()]
        worker.query_device_info(stream,codecs.getincrementaldecoder('utf-8')())
        self.assertTrue(results[-1]['ok']);self.assertFalse(worker.isInterruptionRequested());stream.write.assert_called_once_with(b'device_info\r')

class IdentityHotfixUITests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_complete_unsupported_identity_keeps_console_connected_but_no_capabilities(self):
        worker=Mock();self.w.session=worker;self.w.connected=True;self.w.mode.setCurrentText('CLI');self.w.device_adapter.begin()
        self.w.device_info_finished(worker,{'ok':False,'recoverable':True,'error':'Unsupported hardware identity format.'})
        self.assertTrue(self.w.connected);self.assertIs(self.w.session,worker);self.assertTrue(self.w.send_btn.isEnabled());self.assertTrue(self.w.identify_btn.isEnabled())
        self.assertFalse(self.w.device_adapter.capabilities);self.assertFalse(self.w.gpio_probe_btn.isEnabled());worker.requestInterruption.assert_not_called()
        self.assertIn('unsupported',self.w.connection_message.toolTip());self.w.session=None;self.w.connected=False
