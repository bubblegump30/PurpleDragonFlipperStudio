import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
import test_navigation_memory as navigation

class LogQoLTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_filter_combination_preserves_entries(self):
        self.w.clear_log();self.w.log('USB failed','Error');self.w.log('Other fault','Error');self.w.log('USB ready')
        self.w.log_level.setCurrentText('Error');self.w.log_search.setText('usb')
        self.assertIn('USB failed',self.w.logs.toPlainText());self.assertNotIn('Other fault',self.w.logs.toPlainText())
        self.assertEqual(len(self.w.log_entries),3)
        self.w.log_search.clear();self.w.log_level.setCurrentText('All')
        self.assertIn('USB ready',self.w.logs.toPlainText())
    def test_full_and_visible_exports(self):
        self.w.clear_log();self.w.log('hidden');self.w.log('visible','Error');self.w.log_level.setCurrentText('Error')
        with patch.object(self.w,'export_text') as export:
            self.w.export_log();self.assertIn('hidden',export.call_args.args[0])
            self.w.export_visible_log();self.assertNotIn('hidden',export.call_args.args[0])
        self.w.copy_visible_log();self.assertEqual(QApplication.clipboard().text(),self.w.logs.toPlainText())
    def test_retention_and_clear(self):
        self.w.clear_log()
        for i in range(1003):self.w.log('entry '+str(i))
        self.assertEqual(len(self.w.log_entries),1000)
        self.assertIn('entry 3',self.w.log_entries[0][1]);self.assertIn('1000 visible',self.w.log_count.text())
        self.w.clear_log();self.assertEqual(self.w.logs.toPlainText(),'');self.assertEqual(self.w.log_entries,[])
    def test_live_filtered_error(self):
        self.w.clear_log();self.w.log_level.setCurrentText('Error');self.w.log('ready');self.w.serial_fault('USB gone')
        self.assertIn('[ERROR]',self.w.logs.toPlainText());self.assertNotIn('ready',self.w.logs.toPlainText())
