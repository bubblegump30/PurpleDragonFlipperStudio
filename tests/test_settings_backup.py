import unittest,json,copy
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox
import test_navigation_memory as navigation

class SettingsBackupTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_roundtrip_applies_and_persists(self):
        self.w.profile_name.setText('Example');self.w.notes.setPlainText('notes');self.w.save_profile()
        self.w.ending.setCurrentText('LF');self.w.navigate('UART Console')
        backup=self.w.settings_backup();self.w.new_profile();self.w.ending.setCurrentText('None')
        self.w.restore_settings_backup(backup)
        self.assertEqual(self.w.profiles()['Example']['notes'],'notes')
        self.assertEqual(self.w.ending.currentText(),'LF');self.assertEqual(self.w.workspace.currentText(),'UART Console')
        self.assertIsNone(self.w.session)
        self.w.close();self.w=self.create_window();self.assertEqual(self.w.ending.currentText(),'LF')
    def test_invalid_does_not_mutate(self):
        before=self.w.settings_backup()
        for key,value in [('speed',999),('matrix','true'),('theme','unknown'),('last_workspace','missing')]:
            backup=copy.deepcopy(before);backup['preferences'][key]=value
            with self.assertRaises(ValueError):self.w.restore_settings_backup(backup)
            self.assertEqual(self.w.settings_backup(),before)
        backup=copy.deepcopy(before);backup['schema']=2
        with self.assertRaises(ValueError):self.w.restore_settings_backup(backup)
    def test_restore_cancel_preserves_settings(self):
        before=self.w.settings_backup();backup=copy.deepcopy(before);backup['preferences']['line_ending']='None'
        path=Path(self.temp.name)/'backup.json';path.write_text(json.dumps(backup))
        with patch('purple_dragon.base_window.QFileDialog.getOpenFileName',return_value=(str(path),'')),patch('purple_dragon.base_window.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.w.import_settings_backup()
        self.assertEqual(self.w.settings_backup(),before)
    def test_malformed_file_reports_failure(self):
        path=Path(self.temp.name)/'bad.json';path.write_text('{broken')
        with patch('purple_dragon.base_window.QFileDialog.getOpenFileName',return_value=(str(path),'')),patch.object(self.w,'notify') as notice:
            self.w.import_settings_backup();self.assertEqual(notice.call_args.args[0],'Restore failed')
