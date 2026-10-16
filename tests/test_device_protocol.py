import codecs
import unittest
from unittest.mock import Mock, patch
from purple_dragon.backend import SerialSession
from purple_dragon.device_protocol import DeviceInfoAdapter, parse_device_info, response_complete
import test_navigation_memory as navigation

# Synthetic official-format fixture, not a captured hardware validation.
INFO = ('device_info_major: 2\r\ndevice_info_minor: 4\r\n'
        'hardware_model: Flipper Zero\r\nhardware_uid: 0123456789ABCDEF01234567\r\n'
        'hardware_target: 7\r\nhardware_name: TestDevice\r\n'
        'firmware_version: 1.4.3\r\nfirmware_commit: abc12345\r\n'
        'protobuf_version_major: 0\r\nprotobuf_version_minor: 30\r\n')


class ProtocolTests(unittest.TestCase):
    def test_valid_identity_and_only_implemented_capabilities(self):
        info = parse_device_info(INFO)
        self.assertEqual(info['hardware_name'], 'TestDevice')
        adapter = DeviceInfoAdapter(); adapter.begin()
        self.assertFalse(adapter.capabilities)
        adapter.complete({'ok': True, 'response': INFO})
        self.assertEqual(adapter.capabilities, frozenset({'device_info'}))
        adapter.reset()
        self.assertFalse(adapter.info)
        self.assertFalse(adapter.capabilities)

    def test_rejects_wrong_partial_duplicate_and_oversized_responses(self):
        for text in [INFO.replace('Flipper Zero', 'ESP32'), INFO.replace('hardware_target: 7', 'hardware_target: 9'),
                     INFO.replace('device_info_major: 2', 'device_info_major: 9'), INFO.replace('0123456789ABCDEF01234567', 'invalid'),
                     INFO.split('protobuf_version_minor:')[0], INFO + 'hardware_target: 7\r\n', 'x'*65537]:
            with self.subTest(text=text[:50]), self.assertRaises(ValueError):
                parse_device_info(text)
        self.assertFalse(response_complete(INFO[:-1]))
        self.assertTrue(response_complete(INFO))

    def test_worker_chunked_query_uses_same_stream_and_one_read_only_command(self):
        navigation.NavigationMemoryTests.setUpClass()
        worker = SerialSession('COM_TEST', 230400)
        result = []; worker.device_info_result.connect(result.append)
        chunks = [INFO[:60].encode(), INFO[60:150].encode(), INFO[150:].encode()]
        stream = Mock(in_waiting=0)
        stream.read.side_effect = lambda n: chunks.pop(0)
        worker.query_device_info(stream, codecs.getincrementaldecoder('utf-8')(errors='replace'))
        stream.write.assert_called_once_with(b'device_info\r')
        self.assertTrue(result[0]['ok'])
        self.assertEqual(parse_device_info(result[0]['response'])['hardware_target'], '7')

    def test_timeout_cancellation_and_send_exclusion(self):
        navigation.NavigationMemoryTests.setUpClass()
        worker = SerialSession('COM_TEST', 230400)
        self.assertTrue(worker.request_device_info())
        self.assertFalse(worker.send('must not interleave'))
        self.assertFalse(worker.request_device_info())
        self.assertIsNone(worker.outbox.get_nowait())
        result = []; worker.device_info_result.connect(result.append)
        stream = Mock(in_waiting=0)
        worker.query_device_info(stream, codecs.getincrementaldecoder('utf-8')(), timeout=0)
        self.assertFalse(result[-1]['ok'])
        self.assertIn('timed out', result[-1]['error'])
        self.assertTrue(worker.isInterruptionRequested())
        self.assertFalse(worker.send('must reconnect after timeout'))
        worker2 = SerialSession('COM_TEST', 230400)
        result2 = []; worker2.device_info_result.connect(result2.append)
        cancelled_stream = Mock(in_waiting=0)
        with patch.object(worker2, 'isInterruptionRequested', return_value=True):
            worker2.query_device_info(cancelled_stream, codecs.getincrementaldecoder('utf-8')())
        cancelled_stream.write.assert_not_called()
        self.assertIn('cancelled', result2[-1]['error'])

    def test_busy_console_queue_does_not_start_query(self):
        navigation.NavigationMemoryTests.setUpClass()
        worker = SerialSession('COM_TEST', 230400)
        worker.send('queued')
        self.assertFalse(worker.request_device_info())


class DeviceIntegrationTests(unittest.TestCase):
    setUpClass = classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp = navigation.NavigationMemoryTests.setUp
    create_window = navigation.NavigationMemoryTests.create_window
    tearDown = navigation.NavigationMemoryTests.tearDown

    def test_manual_query_no_startup_query_and_no_interleaved_send(self):
        self.assertIsNone(self.w.session)
        self.assertFalse(self.w.identify_btn.isEnabled())
        worker = Mock(); worker.request_device_info.return_value = True
        self.w.session = worker; self.w.connected = True; self.w.mode.setCurrentText('CLI')
        self.w.identify_device()
        self.assertEqual(self.w.device_adapter.state, 'querying')
        self.w.command.setText('help'); self.w.send_command()
        worker.send.assert_not_called()
        self.w.device_info_finished(worker, {'ok': True, 'response': INFO})
        self.assertIn('TestDevice', self.w.protocol_details.toPlainText())
        self.assertTrue(self.w.send_btn.isEnabled())
        self.assertTrue(all(not x.isEnabled() for x in self.w.gpio_buttons.values()))
        self.w.session = None; self.w.connected = False

    def test_bridge_mode_and_stale_session_result_are_rejected(self):
        worker = Mock(); self.w.session = worker; self.w.connected = True
        self.w.mode.setCurrentText('UART Bridge'); self.w.identify_device()
        worker.request_device_info.assert_not_called()
        self.w.device_info_finished(Mock(), {'ok': True, 'response': INFO})
        self.assertFalse(self.w.device_adapter.capabilities)
        self.w.session = None; self.w.connected = False

    def test_connection_loss_clears_metadata_and_rejects_late_result(self):
        worker = Mock(); self.w.session = worker; self.w.connected = True
        self.w.device_adapter.begin()
        self.w.device_info_finished(worker, {'ok': True, 'response': INFO})
        self.w.connection_lost = True; self.w.serial_finished()
        self.w.device_info_finished(worker, {'ok': True, 'response': INFO})
        self.assertEqual(self.w.protocol_details.toPlainText(), '')
        self.assertFalse(self.w.device_adapter.capabilities)
        self.assertFalse(self.w.identify_btn.isEnabled())

    def test_diagnostics_do_not_include_device_identifiers(self):
        import json
        self.w.device_adapter.complete({'ok': True, 'response': INFO})
        text = json.dumps(self.w.diagnostics())
        self.assertIn('device_info', text)
        self.assertNotIn('TestDevice', text)
        self.assertNotIn('0123456789ABCDEF01234567', text)
