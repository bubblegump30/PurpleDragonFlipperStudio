import unittest
from pathlib import Path
from unittest.mock import patch
import test_navigation_memory as navigation
from purple_dragon.ir_files import inspect_ir
TEXT='Filetype: IR signals file\nVersion: 1\n#\nname: Power\ntype: parsed\nprotocol: NEC\naddress: 00 00 00 00\ncommand: 01 00 00 00\n#\nname: Volume\ntype: raw\nfrequency: 38000\nduty_cycle: 0.33\ndata: 100 200\n'
class IRQoLTests(unittest.TestCase):
    setUpClass=classmethod(navigation.NavigationMemoryTests.setUpClass.__func__)
    setUp=navigation.NavigationMemoryTests.setUp
    create_window=navigation.NavigationMemoryTests.create_window
    tearDown=navigation.NavigationMemoryTests.tearDown
    def test_parsed_and_raw_structure(self):
        entries,warnings=inspect_ir(TEXT);self.assertEqual([e['name'] for e in entries],['Power','Volume']);self.assertEqual(warnings,[])
        self.assertEqual(inspect_ir(TEXT.replace('IR signals file','IR library file'))[1],[])
    def test_missing_and_duplicate_fields(self):
        entries,warnings=inspect_ir('name: Power\ntype: parsed\nprotocol: NEC\nprotocol: NEC\n')
        self.assertTrue(any('duplicate' in w for w in warnings));self.assertTrue(any('address' in w for w in warnings));self.assertTrue(any('header' in w for w in warnings))
    def test_filter_jump_and_failed_open_preserves_file(self):
        path=Path(self.temp.name)/'test.ir';path.write_text(TEXT,encoding='utf-8-sig')
        with patch('purple_dragon.base_window.QFileDialog.getOpenFileName',return_value=(str(path),'')):self.w.open_ir()
        self.w.ir_filter.setText('volume');self.assertEqual(self.w.ir_signals.count(),1)
        self.assertEqual(self.w.ir_preview.textCursor().selectedText(),'name: Volume')
        path.write_bytes(b'\xff\xff')
        with patch('purple_dragon.base_window.QFileDialog.getOpenFileName',return_value=(str(path),'')),patch.object(self.w,'notify'):self.w.open_ir()
        self.assertEqual(self.w.ir_preview.toPlainText(),TEXT)
