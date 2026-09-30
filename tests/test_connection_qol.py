import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from types import SimpleNamespace
from unittest.mock import patch
import test_navigation_memory as navigation
import unittest

class ConnectionQoLTests(unittest.TestCase):
    setUpClass = classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp = navigation.NavigationMemoryTests.setUp
    create_window = navigation.NavigationMemoryTests.create_window
    tearDown = navigation.NavigationMemoryTests.tearDown
    def ports(self):
        return [SimpleNamespace(device=p, description='USB serial', manufacturer='Example', serial_number=p+'-SN') for p in ['COM3', 'COM4']]
    def refresh(self):
        with patch('purple_dragon.base_window.discover_ports', return_value=self.ports()):
            self.w.refresh_ports()
    def test_per_port_preferences(self):
        self.refresh(); self.w.baud.setCurrentText('115200'); self.w.mode.setCurrentText('UART Bridge')
        self.w.port.setCurrentIndex(1); self.w.baud.setCurrentText('9600')
        self.w.port.setCurrentIndex(0)
        self.assertEqual(self.w.baud.currentText(), '115200')
        self.assertEqual(self.w.mode.currentText(), 'UART Bridge')
        self.refresh(); self.assertEqual(self.w.baud.currentText(), '115200')
    def test_metadata_before_connection(self):
        self.refresh()
        self.assertIn('COM3-SN', self.w.device_details.text())
        self.assertIn('Example', self.w.port.toolTip())
        self.assertIsNone(self.w.session)
    def test_discovery_error_recovery(self):
        self.refresh()
        with patch('purple_dragon.base_window.discover_ports', side_effect=OSError('USB failure')):
            self.w.refresh_ports()
        self.assertFalse(self.w.connect_btn.isEnabled())
        self.assertEqual(self.w.port_info, {})
        self.assertIn('USB failure', self.w.connection_message.toolTip())
        self.refresh(); self.assertTrue(self.w.connect_btn.isEnabled())
    def test_fault_survives_thread_finish(self):
        self.refresh(); self.w.serial_fault('port busy'); self.w.serial_finished()
        self.assertIn('port busy', self.w.connection_message.text())
        self.assertEqual(self.w.connect_btn.text(), 'Retry')
        self.assertIn('ERROR', self.w.badge.text())
        self.assertFalse(self.w.send_btn.isEnabled())
    def test_cancel_ignores_late_open(self):
        self.refresh(); self.w.connection_cancelled=True; self.w.serial_opened()
        self.assertFalse(self.w.connected)
        self.assertFalse(self.w.send_btn.isEnabled())

