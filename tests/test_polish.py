import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from purple_dragon.window import MainWindow
from purple_dragon.neon import NeonButton

class PolishTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.settings=QSettings(str(Path(self.temp.name)/'settings.ini'),QSettings.IniFormat)
  with patch('purple_dragon.base_window.discover_ports',return_value=[]):self.w=MainWindow(settings=self.settings)
  self.w.show();self.app.processEvents()
 def tearDown(self):self.w.close();self.app.processEvents();self.temp.cleanup()
 def test_window_geometry_saved_and_restored(self):
  self.w.resize(1200,850);self.w.close();self.app.processEvents()
  self.assertTrue(self.settings.value('window_geometry'))
  with patch('purple_dragon.base_window.discover_ports',return_value=[]):other=MainWindow(settings=self.settings)
  self.assertTrue(other.geometry_restored);other.close()
 def test_button_tooltips_and_disabled_explanations(self):
  for button in self.w.findChildren(NeonButton):self.assertTrue(button.toolTip(),button.text())
  self.assertIn('backend',self.w.arm.toolTip())
  self.assertIn('backend',self.w.poll.toolTip())
 def test_resize_stays_usable(self):
  self.w.resize(980,760);self.app.processEvents()
  self.assertEqual(self.w.stack.currentWidget().horizontalScrollBar().maximum(),0)
if __name__=='__main__':unittest.main()
