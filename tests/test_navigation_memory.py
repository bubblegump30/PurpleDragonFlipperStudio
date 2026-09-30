import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QSettings,Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from purple_dragon.window import MainWindow


class NavigationMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.settings=QSettings(str(Path(self.temp.name)/'settings.ini'),QSettings.IniFormat)
        self.w=self.create_window()
    def create_window(self):
        with patch('purple_dragon.base_window.discover_ports',return_value=[]):
            w=MainWindow(settings=self.settings)
        w.show();w.activateWindow();self.app.processEvents();return w
    def tearDown(self):self.w.close();self.app.processEvents();self.temp.cleanup()
    def test_saved_workspace_restores_without_connection(self):
        self.w.navigate('IR Remote Studio');self.w.close()
        self.w=self.create_window()
        self.assertEqual(self.w.workspace.currentText(),'IR Remote Studio')
        self.assertTrue(self.w.nav['IR Remote Studio'].isChecked())
        self.assertTrue(self.w.tab_buttons['IR Remote Studio'].isChecked())
        self.assertIsNone(self.w.session)
        self.assertFalse(self.w.connected)
    def test_invalid_saved_workspace_falls_back(self):
        self.w.close();self.settings.setValue('last_workspace','Deleted page')
        self.w=self.create_window()
        self.assertEqual(self.w.workspace.currentText(),'GPIO Lab')
        self.assertTrue(self.w.nav['Command Center'].isChecked())
    def test_history_and_branching(self):
        self.w.navigate('UART Console');self.w.navigate('Apps & NFC')
        self.w.travel(-1)
        self.assertEqual(self.w.workspace.currentText(),'UART Console')
        self.assertTrue(self.w.shortcut_actions['Forward'].isEnabled())
        self.w.navigate('Live Log')
        self.assertFalse(self.w.shortcut_actions['Forward'].isEnabled())
        self.assertNotIn('Apps & NFC',self.w.navigation_history)
    def test_alias_and_repeated_selection_do_not_add_history(self):
        self.w.navigate('GPIO Lab');self.w.navigate('GPIO Lab')
        self.assertEqual(len(self.w.navigation_history),1)
    def test_keyboard_shortcuts(self):
        QTest.keyClick(self.w,Qt.Key.Key_2,Qt.KeyboardModifier.ControlModifier)
        self.app.processEvents()
        self.assertEqual(self.w.workspace.currentText(),'UART Console')
        QTest.keyClick(self.w,Qt.Key.Key_L,Qt.KeyboardModifier.ControlModifier)
        self.app.processEvents();self.assertTrue(self.w.command.hasFocus())
        QTest.keyClick(self.w,Qt.Key.Key_Home,Qt.KeyboardModifier.ControlModifier)
        self.app.processEvents();self.assertEqual(self.w.workspace.currentText(),'GPIO Lab')
