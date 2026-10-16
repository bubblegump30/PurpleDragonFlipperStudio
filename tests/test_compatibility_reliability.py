import codecs
import json
import unittest
from unittest.mock import Mock, patch
from purple_dragon.backend import SerialSession
from purple_dragon.compatibility import compatibility_snapshot
from purple_dragon.device_protocol import DeviceInfoAdapter, parse_device_info
from purple_dragon.sd_protocol import StorageClient, StorageError
from test_device_protocol import INFO
import test_navigation_memory as navigation


class ReliabilityProtocolTests(unittest.TestCase):
    def test_interrupted_worker_rejects_all_new_work(self):
        worker=SerialSession('test',115200);worker.requestInterruption()
        self.assertFalse(worker.send('help'));self.assertFalse(worker.request_device_info())
        self.assertFalse(worker.request_storage('gpio_probe','/ext'));self.assertTrue(worker.outbox.empty())
        with patch('purple_dragon.backend.serial.Serial') as factory:worker.run()
        factory.assert_not_called()
    def test_request_snapshots_mutable_payload(self):
        worker=SerialSession('test',115200);request={'entry':{'fields':{'command':'original'}}}
        self.assertTrue(worker.request_storage('ir_transmit','/ext',request));request['entry']['fields']['command']='changed'
        self.assertEqual(worker.outbox.get_nowait()['local']['entry']['fields']['command'],'original')
    def test_copy_failure_does_not_lock_queue(self):
        worker=SerialSession('test',115200)
        with patch('purple_dragon.backend.copy.deepcopy',side_effect=ValueError('copy failed')):
            with self.assertRaises(ValueError):worker.request_storage('test','/ext',{})
        self.assertFalse(worker.query_pending);self.assertTrue(worker.request_device_info())
    def test_timeout_and_os_error_close_identity_session(self):
        for failure in [None,OSError('USB lost')]:
            worker=SerialSession('test',115200);result=[];worker.device_info_result.connect(result.append)
            stream=Mock(in_waiting=0)
            if failure:stream.write.side_effect=failure
            worker.query_device_info(stream,codecs.getincrementaldecoder('utf-8')(),timeout=0)
            self.assertFalse(result[-1]['ok']);self.assertTrue(worker.isInterruptionRequested());self.assertFalse(worker.send('retry'))
    def test_failed_operation_does_not_read_again_before_closing(self):
        worker=SerialSession('test',115200);worker.request_storage('unknown','/ext')
        stream=Mock(in_waiting=0);context=Mock();context.__enter__=Mock(return_value=stream);context.__exit__=Mock(return_value=False)
        with patch('purple_dragon.backend.serial.Serial',return_value=context):worker.run()
        stream.read.assert_not_called();self.assertTrue(worker.isInterruptionRequested())

    def test_protocol_rejects_nontext_and_bad_result(self):
        for value in [None,{},b'not decoded',12]:
            with self.assertRaises(ValueError):parse_device_info(value)
        adapter=DeviceInfoAdapter();adapter.complete(None);self.assertEqual(adapter.state,'unsupported')
    def test_echo_must_match_command_not_just_suffix(self):
        stream=Mock(in_waiting=0);stream.write.side_effect=len
        stream.read.side_effect=[b'not-gpio\r\n',b'gpio\r\n']
        client=StorageClient(stream);client.header('gpio');self.assertEqual(stream.read.call_count,2)
    def test_prompt_does_not_discard_error_as_a_hostname(self):
        client=StorageClient(Mock(in_waiting=0,read=Mock(return_value=b'')));client.buffer=b'Storage error: failed\r\n>: '
        self.assertEqual(client.finish(),b'Storage error: failed')
        client.buffer=b'Storage error: failed>: '
        with patch('purple_dragon.sd_protocol.time.monotonic',side_effect=iter(range(0,100,10))):
            with self.assertRaises(StorageError):client.finish()

class CompatibilityTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def ready(self):
        self.worker=Mock();self.w.session=self.worker;self.w.connected=True;self.w.connection_state='connected';self.w.mode.setCurrentText('CLI')
        self.w.device_adapter.complete({'ok':True,'response':INFO});self.w.update_sd_controls();self.addCleanup(self.clear)
    def clear(self):self.w.session=None;self.w.connected=False
    def test_report_no_startup_commands_or_device_identifiers(self):
        self.w.run_local_checks();self.assertIsNone(self.w.session)
        self.ready();report=compatibility_snapshot(self.w);text=json.dumps(report)
        self.assertNotIn('TestDevice',text);self.assertNotIn('0123456789ABCDEF01234567',text)
        self.assertEqual(report['capabilities'][0]['status'],'Checked this session')
        self.assertEqual(report['capabilities'][1]['status'],'Not checked');self.worker.request_storage.assert_not_called()
    def test_capabilities_are_observed_not_inferred_from_firmware(self):
        self.ready();self.w.device_adapter.capabilities|={'sd_files','ir_tx','gpio_digital'};self.w.update_sd_controls()
        self.assertEqual([self.w.compatibility_table.topLevelItem(i).text(1) for i in range(4)],['Checked this session']*4)
        self.w.reset_device_identity();self.assertTrue(all(x['status']=='Not checked' for x in compatibility_snapshot(self.w)['capabilities'][:4]))
    def test_manual_send_invalidates_every_device_capability(self):
        self.ready();self.w.device_adapter.capabilities|={'sd_files','ir_tx','gpio_digital'};self.w.sd_available=True
        self.w.ir_capabilities={'raw':True,'protocols':['NEC']};self.w.gpio_supported=True
        self.w.command.setText('help');self.w.send_command()
        self.assertFalse(self.w.device_adapter.capabilities);self.assertFalse(self.w.sd_available);self.assertIsNone(self.w.ir_capabilities)
        self.assertFalse(self.w.gpio_supported);self.assertTrue(self.w.identify_btn.isEnabled());self.worker.request_storage.assert_not_called()
    def test_old_transport_signals_cannot_touch_replacement_session(self):
        from types import SimpleNamespace
        ports=[SimpleNamespace(device='COM3',description='test',manufacturer=None,serial_number=None)]
        old=SerialSession('COM3',115200);current=SerialSession('COM3',115200)
        with patch('purple_dragon.base_window.discover_ports',return_value=ports):
            self.w.refresh_ports()
            with patch('purple_dragon.base_window.SerialSession',return_value=old),patch.object(old,'start'):
                self.w.toggle_connection()
            old.opened.emit();self.assertTrue(self.w.connected);old.finished.emit()
            with patch('purple_dragon.base_window.SerialSession',return_value=current),patch.object(current,'start'):
                self.w.toggle_connection()
        old.opened.emit();old.received.emit('STALE_BYTES');old.fault.emit('stale fault');old.finished.emit()
        self.assertIs(self.w.session,current);self.assertFalse(self.w.connected);self.assertIsNone(self.w.last_connection_error)
        self.assertNotIn('STALE_BYTES',self.w.raw_transcript());current.opened.emit();self.assertTrue(self.w.connected)
        self.w.session=None;self.w.connected=False
    def test_failed_operation_retains_cause_and_invalidates_all_capabilities(self):
        self.ready();self.w.start_gpio_operation('gpio_probe')
        self.w.deliver_operation_result(self.worker,{'operation':'gpio_probe','ok':False,'error':'Unsupported GPIO response'})
        self.assertIn('Unsupported GPIO',self.w.last_connection_error);self.assertFalse(self.w.device_adapter.capabilities)
        self.assertFalse(self.w.gpio_probe_btn.isEnabled());self.worker.requestInterruption.assert_called()
        self.w.serial_finished();self.assertIn('Unsupported GPIO',self.w.connection_message.toolTip())
    def test_late_operation_error_cannot_fault_new_session(self):
        self.ready();self.w.deliver_operation_result(Mock(),{'operation':'gpio_probe','ok':False,'error':'stale'})
        self.assertIsNone(self.w.last_connection_error);self.worker.requestInterruption.assert_not_called()
    def test_local_corrupt_store_reported_without_mutation(self):
        self.w.settings.setValue('ir_libraries','broken');self.w.run_local_checks()
        report=compatibility_snapshot(self.w);self.assertFalse(next(x['ok'] for x in report['local_checks'] if x['area']=='IR library store'))
        self.assertEqual(self.w.settings.value('ir_libraries'),'broken');self.assertIn('needs attention',self.w.compatibility_recovery.text())
    def test_export_report_uses_snapshot_and_no_device_commands(self):
        self.ready()
        with patch.object(self.w,'export_text') as export:self.w.export_compatibility()
        report=json.loads(export.call_args.args[0]);self.assertEqual(report['schema'],1);self.worker.request_storage.assert_not_called()
        self.assertIn('compatibility',self.w.diagnostics())
    def test_query_failure_blocks_send_and_preserves_reconnect_reason(self):
        self.ready();self.w.device_adapter.begin();self.w.device_info_finished(self.worker,{'ok':False,'error':'identity timed out'})
        self.assertFalse(self.w.send_btn.isEnabled());self.assertFalse(self.w.identify_btn.isEnabled());self.assertIn('identity timed out',self.w.last_connection_error)
