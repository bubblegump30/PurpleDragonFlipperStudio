import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import setup_bootstrap as setup


def info(version, bits=64, free=False):
    return {'version': list(version), 'bits': bits, 'implementation': 'CPython', 'free_threaded': free}


class SetupTests(unittest.TestCase):
    def test_python_314_supported(self):
        self.assertTrue(setup.supported(info((3,14))))
        self.assertTrue(setup.supported(info((3,10))))
        self.assertFalse(setup.supported(info((3,15))))
        self.assertFalse(setup.supported(info((3,9))))
        self.assertFalse(setup.supported(info((3,14),32)))
        self.assertFalse(setup.supported(info((3,14),free=True)))

    def test_skip_incompatible_default_and_choose_supported(self):
        commands = [['default-3.15'], ['py','-3.14'], ['py','-3.12']]
        available = {'default-3.15': None, '-3.14': info((3,14)), '-3.12': info((3,12))}
        command, result = setup.choose_interpreter(commands, lambda c: available[c[-1]])
        self.assertEqual(command, ['py','-3.14'])
        self.assertEqual(result['version'], [3,14])

    def test_existing_314_environment_is_reused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            executable = setup.environment_python(root)
            executable.parent.mkdir(parents=True)
            executable.touch()
            def never_run(*args, **kwargs):
                self.fail('Compatible environments must not be recreated.')
            result = setup.prepare_environment(root, [], lambda c: info((3,14)), never_run)
            self.assertEqual(result, executable)

    def test_incompatible_environment_is_preserved_and_rebuilt(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            executable = setup.environment_python(root)
            executable.parent.mkdir(parents=True)
            executable.touch()
            (root/'.venv'/'marker.txt').write_text('preserve me')
            rebuilt = []
            def check(command):
                return info((3,12)) if command == ['chosen'] or rebuilt else None
            def run(command, **kwargs):
                self.assertEqual(command[:3], ['chosen','-m','venv'])
                executable.parent.mkdir(parents=True)
                executable.touch()
                rebuilt.append(True)
                return SimpleNamespace(returncode=0)
            setup.prepare_environment(root, [['chosen']], check, run)
            backups = list(root.glob('.venv.previous-*'))
            self.assertEqual(len(backups),1)
            self.assertEqual((backups[0]/'marker.txt').read_text(), 'preserve me')
            self.assertTrue(executable.exists())

    def test_missing_interpreter_keeps_existing_environment(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root/'.venv').mkdir()
            marker = root/'.venv'/'marker.txt'
            marker.write_text('keep')
            with self.assertRaises(RuntimeError):
                setup.prepare_environment(root, [['missing']], lambda c: None)
            self.assertEqual(marker.read_text(), 'keep')
            self.assertFalse(list(root.glob('.venv.previous-*')))

    def test_real_probe_current_python(self):
        import sys
        self.assertIsNotNone(setup.probe([sys.executable]))


if __name__ == '__main__':
    unittest.main()
