import unittest
from unittest.mock import Mock
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import test_navigation_memory as navigation

class ConsoleQoLTests(unittest.TestCase):
    setUpClass = classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp = navigation.NavigationMemoryTests.setUp
    create_window = navigation.NavigationMemoryTests.create_window
    tearDown = navigation.NavigationMemoryTests.tearDown
    def send(self, text, success=True):
        session=Mock(); session.send.return_value=success
        self.w.session=session; self.w.connected=True; self.w.command.setText(text)
        self.w.send_command(); self.w.session=None; self.w.connected=False
        return session
    def test_history_recall_and_draft_without_transmission(self):
        session=self.send('help'); self.send('version')
        self.w.command.setText('draft')
        QTest.keyClick(self.w.command, Qt.Key.Key_Up)
        self.assertEqual(self.w.command.text(),'version')
        QTest.keyClick(self.w.command, Qt.Key.Key_Up)
        self.assertEqual(self.w.command.text(),'help')
        QTest.keyClick(self.w.command, Qt.Key.Key_Down)
        QTest.keyClick(self.w.command, Qt.Key.Key_Down)
        self.assertEqual(self.w.command.text(),'draft')
        self.assertEqual(session.send.call_count,1)
    def test_failed_queue_keeps_draft_and_history(self):
        self.send('retry me',False)
        self.assertEqual(self.w.command.text(),'retry me')
        self.assertEqual(self.w.command_history,[])
    def test_history_bounded_and_clear(self):
        for i in range(105):self.send(str(i))
        self.assertEqual(len(self.w.command_history),100)
        self.send('104');self.assertEqual(len(self.w.command_history),100)
        self.w.clear_command_history();self.assertEqual(self.w.command_history,[])
    def test_search_wrap_and_missing(self):
        self.w.receive('alpha beta alpha')
        self.w.console_search.setText('alpha')
        for _ in range(3):
            self.w.find_console();self.assertEqual(self.w.console.textCursor().selectedText(),'alpha')
        self.w.find_console(True);self.assertEqual(self.w.console.textCursor().selectedText(),'alpha')
        self.w.console_search.setText('missing');self.w.find_console()
        self.assertEqual(self.w.search_feedback.text(),'No match')
    def test_preferences_restore_and_exact_send(self):
        self.w.ending.setCurrentText('LF');self.w.console_scroll.setChecked(False)
        session=self.send('hello');session.send.assert_called_once_with('hello\n')
        self.w.close();self.w=self.create_window()
        self.assertEqual(self.w.ending.currentText(),'LF')
        self.assertFalse(self.w.console_scroll.isChecked())
        self.assertEqual(self.w.command_history,[])
    def test_scroll_pause_preserves_selection(self):
        self.w.console_scroll.setChecked(False);self.w.receive('alpha beta')
        self.w.console_search.setText('alpha');self.w.find_console()
        self.w.receive(' gamma')
        self.assertEqual(self.w.console.textCursor().selectedText(),'alpha')
