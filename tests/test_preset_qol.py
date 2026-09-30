import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox
import test_navigation_memory as navigation

class PresetQoLTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def seed(self):
        self.w.profile_name.setText('Original');self.w.notes.setPlainText('Keep notes');self.w.save_profile()
    def test_duplicate_unique_and_preserved(self):
        self.seed();original=self.w.profiles()['Original'].copy()
        self.w.duplicate_profile();self.assertEqual(self.w.profiles()['Original copy'],original)
        self.w.refresh_profiles('Original');self.w.duplicate_profile()
        self.assertIn('Original copy 2',self.w.profiles())
        self.assertEqual(self.w.profiles()['Original'],original)
    def test_rename_preserves_saved_fields(self):
        self.seed();self.w.profile_name.setText('Renamed');self.w.rename_profile()
        self.assertNotIn('Original',self.w.profiles())
        self.assertEqual(self.w.profiles()['Renamed']['notes'],'Keep notes')
        self.assertEqual(self.w.profile.currentData(),'Renamed')
    def test_new_leaves_saved_data(self):
        self.seed();self.w.new_profile()
        self.assertEqual(self.w.profile_name.text(),'')
        self.assertEqual(self.w.notes.toPlainText(),'')
        self.assertIn('Original',self.w.profiles())
    def test_collision_rejected_and_overwrite_cancelled(self):
        self.seed();self.w.duplicate_profile();self.w.profile_name.setText('Original')
        before=self.w.profiles()
        with patch.object(self.w,'notify'):self.w.rename_profile()
        self.assertEqual(self.w.profiles(),before)
        self.w.notes.setPlainText('replacement')
        with patch('purple_dragon.base_window.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.w.save_profile()
        self.assertEqual(self.w.profiles(),before)
    def test_duplicate_limit(self):
        import json
        self.w.settings.setValue('profiles',json.dumps({str(i):{'pin':self.w.pin.currentText(),'notes':''} for i in range(200)}))
        self.w.refresh_profiles('0')
        with patch.object(self.w,'notify') as notice:self.w.duplicate_profile();notice.assert_called_once()
        self.assertEqual(len(self.w.profiles()),200)
