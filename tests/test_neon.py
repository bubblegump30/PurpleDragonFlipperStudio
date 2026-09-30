import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QSettings, QUrl
from PySide6.QtWidgets import QApplication, QFileDialog
from purple_dragon.window import MainWindow
from purple_dragon.theme import THEMES
from purple_dragon.neon import NeonButton, NeonPanel


class NeonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        with patch('purple_dragon.base_window.discover_ports',return_value=[]):
            self.w=MainWindow(settings=QSettings(str(Path(self.temp.name)/'settings.ini'),QSettings.IniFormat))
        self.w.show();self.app.processEvents()

    def tearDown(self):self.w.close();self.app.processEvents();self.temp.cleanup()

    def test_sidebar_tabs_and_workspace_follow_selection(self):
        self.w.tab_buttons['UART Console'].click();self.app.processEvents()
        self.assertEqual(self.w.workspace.currentText(),'UART Console')
        self.assertTrue(self.w.nav['UART Console'].isChecked())
        self.w.workspace.setCurrentText('GPIO Lab');self.app.processEvents()
        self.assertTrue(self.w.tab_buttons['GPIO Lab'].isChecked())
        self.w.nav['Command Center'].click()
        self.assertEqual(self.w.stack.currentIndex(),self.w.pages['GPIO Lab'])

    def test_inline_theme_changes_controls_panels_and_matrix(self):
        self.w.inline_theme.setCurrentText('Electric Cyan')
        self.assertEqual(self.w.theme.currentText(),'Electric Cyan')
        self.assertEqual(self.w.rain.color.name(),THEMES['Electric Cyan'])
        for item in self.w.findChildren(NeonPanel)+self.w.findChildren(NeonButton):
            self.assertEqual(item.accent,THEMES['Electric Cyan'])
        self.w.glow.setChecked(False)
        self.assertFalse(self.w.gpio_buttons['Input'].glow)

    def test_responsive_pages_have_no_horizontal_overflow(self):
        for size in [(980,760),(1672,941)]:
            self.w.resize(*size);self.app.processEvents()
            for name in self.w.pages:
                self.w.navigate(name);self.app.processEvents()
                self.assertEqual(self.w.stack.currentWidget().horizontalScrollBar().maximum(),0,name)

    def test_disconnected_hardware_actions_are_gated(self):
        for item in self.w.gpio_buttons.values():self.assertFalse(item.isEnabled())
        self.assertFalse(self.w.arm.isEnabled())
        self.assertFalse(self.w.poll.isEnabled())
        self.w.pin.setCurrentText('PC0 (pin 16)')
        self.assertEqual(self.w.pin_value.text(),'PC0 (pin 16)')

    def test_gpio_history_export(self):
        self.w.history.setPlainText('local history test')
        path=Path(self.temp.name)/'history.txt'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'Text')):self.w.export_history()
        self.assertEqual(path.read_text(),'local history test')


if __name__=='__main__':unittest.main()
