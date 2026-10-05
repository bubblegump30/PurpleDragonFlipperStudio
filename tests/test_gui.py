import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog
from purple_dragon.window import MainWindow
from purple_dragon.backend import SerialSession
from purple_dragon.theme import THEMES
import serial


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.temp.name) / 'settings.ini'
        self.settings = QSettings(str(self.settings_path), QSettings.Format.IniFormat)
        with patch('purple_dragon.base_window.discover_ports', return_value=[]):
            self.window = MainWindow(settings=self.settings)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def pump(self, predicate, timeout=2):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            time.sleep(.01)
        self.fail('Timed out waiting for worker signal.')

    def test_no_port_state_and_navigation(self):
        self.assertFalse(self.window.connect_btn.isEnabled())
        self.assertFalse(self.window.send_btn.isEnabled())
        self.assertEqual(self.window.stack.count(), 9)
        for name in self.window.pages:
            self.window.nav[name].click()
            self.app.processEvents()
            self.assertEqual(self.window.stack.currentIndex(), self.window.pages[name])
            self.assertEqual(self.window.heading.text(), "GPIO Lab" if name == "Command Center" else name)

    def test_theme_and_motion_persist(self):
        for name in THEMES:
            self.window.theme.setCurrentText(name)
            self.assertEqual(self.window.rain.color.name(), THEMES[name])
        self.window.reduced.setChecked(True)
        self.assertFalse(self.window.rain.timer.isActive())
        self.settings.sync()
        saved = QSettings(str(self.settings_path), QSettings.Format.IniFormat)
        self.assertEqual(saved.value('theme'), 'Solar Gold')
        self.assertTrue(saved.value('reduced', False, type=bool))
        self.window.reset_appearance()
        self.assertEqual(self.window.theme.currentText(), 'Neo Purple')

    def test_profile_save_and_roundtrip_import_export(self):
        self.window.profile_name.setText('Desk sensor')
        self.window.notes.setPlainText('Use compatible input only.')
        self.window.save_profile()
        expected = self.window.profiles()
        destination = str(Path(self.temp.name) / 'setups.json')
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(destination, 'JSON')):
            self.window.export_profiles()
        self.assertEqual(json.loads(Path(destination).read_text()), expected)
        self.settings.setValue('profiles', '{}')
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(destination, 'JSON')):
            self.window.import_profiles()
        self.assertEqual(self.window.profiles(), expected)

    def test_malformed_profiles_are_rejected(self):
        for data in [[], {'bad': {}}, {'bad': {'pin': 5, 'notes': 'x'}}]:
            with self.assertRaises(ValueError):
                self.window.validate_profiles(data)

    def test_ir_preview_and_transcript_export(self):
        source = Path(self.temp.name) / 'remote.ir'
        source.write_text('Filetype: IR signals file\nVersion: 1\n', encoding='utf-8')
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(source), 'IR')):
            self.window.open_ir()
        self.assertIn('IR signals', self.window.ir_preview.toPlainText())
        self.window.receive('test serial output\r\n')
        destination = Path(self.temp.name) / 'console.txt'
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(destination), 'Text')):
            self.window.export_console()
        self.assertIn('test serial output', destination.read_text())

    def test_disappeared_saved_port(self):
        self.settings.setValue('port', 'COM3')
        with patch('purple_dragon.base_window.discover_ports', return_value=[]):
            self.window.refresh_ports()
        self.assertIn('COM3 is unavailable', self.window.connection_message.text())
        self.assertFalse(self.window.connect_btn.isEnabled())

    def test_connection_failure_recovers(self):
        info = SimpleNamespace(device='COM_TEST', description='Test', manufacturer=None, serial_number=None)
        with patch('purple_dragon.base_window.discover_ports', return_value=[info]):
            self.window.refresh_ports()
        with patch('purple_dragon.base_window.discover_ports', return_value=[info]), patch('purple_dragon.backend.serial.Serial', side_effect=serial.SerialException('port busy')):
            self.window.toggle_connection()
            self.pump(lambda: self.window.session is None)
        self.assertFalse(self.window.connected)
        self.assertFalse(self.window.send_btn.isEnabled())
        self.assertTrue(self.window.port.isEnabled())
        self.assertIn('port busy', self.window.logs.toPlainText())

    def test_serial_worker_loopback_and_shutdown(self):
        # Exercise the real pySerial API through its local loopback transport.
        original = serial.serial_for_url
        received = []
        opened = []
        worker = SerialSession('loop://', 115200)
        worker.opened.connect(lambda: opened.append(True))
        worker.received.connect(received.append)
        with patch('purple_dragon.backend.serial.Serial', side_effect=lambda port, baud, **kwargs: original(port, baudrate=baud, **kwargs)):
            worker.start()
            try:
                self.pump(lambda: bool(opened))
                worker.send('hello π\r\n')
                self.pump(lambda: 'hello π' in ''.join(received))
            finally:
                worker.requestInterruption()
                self.assertTrue(worker.wait(1500))
        self.assertFalse(worker.isRunning())


if __name__ == '__main__':
    unittest.main()
