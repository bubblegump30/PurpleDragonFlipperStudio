import unittest,json
from pathlib import Path
from unittest.mock import patch
import test_navigation_memory as navigation

class ReliabilityTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_diagnostics_metadata_without_user_content(self):
        self.w.profile_name.setText('Private preset');self.w.notes.setPlainText('private notes');self.w.save_profile()
        self.w.receive('private serial text');self.w.log('private log message');self.w.last_connection_error='private USB identifier'
        report=self.w.diagnostics();text=json.dumps(report)
        for secret in ['Private preset','private notes','private serial text','private log message','private USB identifier']:
            self.assertNotIn(secret,text)
        self.assertTrue(report['settings']['preset_store_valid']);self.assertEqual(report['settings']['preset_count'],1)
        self.assertEqual(report['version'],__import__('purple_dragon').__version__);self.assertTrue(report['connection']['last_error_present'])
    def test_atomic_export_failure_preserves_file(self):
        path=Path(self.temp.name)/'export.txt';path.write_text('original')
        with patch('purple_dragon.base_window.os.replace',side_effect=OSError('locked')):
            with self.assertRaises(OSError):self.w.atomic_write_text(path,'replacement')
        self.assertEqual(path.read_text(),'original');self.assertEqual(list(Path(self.temp.name).glob('.purple-dragon-*')),[])
        self.w.atomic_write_text(path,'replacement');self.assertEqual(path.read_text(),'replacement')
    def test_corrupt_presets_preserved_until_restore(self):
        backup=self.w.settings_backup();self.w.settings.setValue('profiles','{broken')
        self.w.profile_name.setText('new')
        with patch.object(self.w,'notify') as notice:
            self.w.save_profile();self.w.import_profiles();self.w.export_settings_backup();self.assertEqual(notice.call_count,3)
        self.assertEqual(self.w.settings.value('profiles'),'{broken')
        self.assertFalse(self.w.diagnostics()['settings']['preset_store_valid'])
        self.w.restore_settings_backup(backup);self.assertTrue(self.w.diagnostics()['settings']['preset_store_valid'])
    def test_export_failure_feedback(self):
        path=Path(self.temp.name)/'export.txt';path.write_text('original')
        with patch('purple_dragon.base_window.QFileDialog.getSaveFileName',return_value=(str(path),'')),patch.object(self.w,'atomic_write_text',side_effect=OSError('disk error')),patch.object(self.w,'notify') as notice:
            self.w.export_diagnostics();self.assertEqual(notice.call_args.args[0],'Export failed')
        self.assertEqual(path.read_text(),'original')
