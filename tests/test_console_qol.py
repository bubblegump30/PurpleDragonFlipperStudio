import unittest
import json
from pathlib import Path
from PySide6.QtWidgets import QFileDialog
from unittest.mock import Mock, patch
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

    def test_favorites_persist_and_load_never_sends(self):
        self.w.command.setText('status')
        self.w.save_command_favorite()
        self.w.save_command_favorite()
        self.assertEqual(self.w.favorite_commands(), ['status'])
        self.w.close(); self.w = self.create_window()
        self.w.session = Mock()
        self.w.command_favorites.setCurrentIndex(1)
        self.w.load_command_favorite()
        self.assertEqual(self.w.command.text(), 'status')
        self.w.session.send.assert_not_called()
        self.w.session = None
        self.w.remove_command_favorite()
        self.assertEqual(self.w.favorite_commands(), [])

    def test_corrupt_favorites_preserved(self):
        self.w.settings.setValue('command_favorites', '{bad')
        self.w.command.setText('help')
        with patch.object(self.w, 'notify') as notice:
            self.w.save_command_favorite()
        notice.assert_called_once()
        self.assertEqual(self.w.settings.value('command_favorites'), '{bad')

    def test_pause_captures_and_resume_renders_without_send(self):
        self.w.receive('before')
        self.w.console_pause.setChecked(True)
        self.w.receive(' during')
        self.assertEqual(self.w.console.toPlainText(), 'before')
        self.assertEqual(self.w.raw_transcript(), 'before during')
        self.w.console_pause.setChecked(False)
        self.assertEqual(self.w.console.toPlainText(), 'before during')
        self.assertIsNone(self.w.session)

    def test_timestamps_do_not_change_raw_and_restore(self):
        self.w.receive('split')
        self.w.receive(' line\r\n')
        self.w.console_timestamps.setChecked(True)
        self.assertIn('received_at', self.w.transcript_records[0])
        self.assertIn('[', self.w.console.toPlainText())
        self.assertEqual(self.w.raw_transcript(), 'split line\r\n')
        self.w.console_timestamps.setChecked(False)
        self.assertEqual(self.w.console.toPlainText(), 'split line\n')
        self.w.console_timestamps.setChecked(True)
        self.w.close(); self.w = self.create_window()
        self.assertTrue(self.w.console_timestamps.isChecked())
        self.assertFalse(self.w.console_pause.isChecked())

    def test_pause_capture_bounded_and_clear(self):
        self.w.console_pause.setChecked(True)
        for i in range(2005):
            self.w.receive('x')
        self.assertEqual(len(self.w.transcript_records), 2000)
        self.assertTrue(self.w.transcript_trimmed)
        self.w.receive('y' * 200001)
        self.assertLessEqual(self.w.transcript_characters, 200000)
        self.w.clear_console()
        self.w.console_pause.setChecked(False)
        self.assertEqual(self.w.raw_transcript(), '')
        self.assertFalse(self.w.transcript_trimmed)

    def test_export_captures_paused_data_as_raw_or_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            self.w.console_pause.setChecked(True)
            self.w.receive('alpha\r\nbeta')
            raw = Path(folder) / 'capture.txt'
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(raw), 'Plain text (*.txt)')):
                self.w.export_console()
            self.assertEqual(raw.read_bytes(), b'alpha\r\nbeta')
            structured = Path(folder) / 'capture.json'
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(structured), 'Timestamped JSON (*.json)')):
                self.w.export_console()
            data = json.loads(structured.read_text())
            self.assertEqual(data['records'][0]['text'], 'alpha\r\nbeta')
            self.assertIn('received_at', data['records'][0])
            self.assertFalse(data['trimmed'])
