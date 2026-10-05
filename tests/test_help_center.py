import unittest
from unittest.mock import Mock
import test_navigation_memory as navigation

class HelpCenterTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_open_reuses_dialog_and_preserves_workspace(self):
        self.w.navigate('UART Console');self.w.beginner_guide();dialog=self.w.help_center
        self.w.beginner_guide();self.assertIs(self.w.help_center,dialog)
        self.assertEqual(self.w.workspace.currentText(),'UART Console');self.assertTrue(dialog.isVisible())
    def test_search_all_topics_and_clear(self):
        self.w.beginner_guide();dialog=self.w.help_center;dialog.search.setText('retry')
        self.assertIn('Troubleshooting',dialog.text.toPlainText());self.assertFalse(dialog.topic.isEnabled())
        dialog.search.setText('no-such-help-topic');self.assertIn('No matching',dialog.text.toPlainText())
        dialog.search.clear();self.assertTrue(dialog.topic.isEnabled())
    def test_capability_guidance_and_no_send(self):
        self.w.beginner_guide();dialog=self.w.help_center;dialog.topic.setCurrentText('Release and capabilities')
        self.assertIn('require RC7',dialog.text.toPlainText());self.assertIn('Physical hardware integration remains unverified',dialog.text.toPlainText())
        self.assertIsNone(self.w.session)
