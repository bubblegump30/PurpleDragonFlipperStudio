import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('release_package', Path(__file__).resolve().parents[1] / 'scripts/package_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleasePackagingTests(unittest.TestCase):
    def test_archives_share_commit_and_checksums_and_exclude_untracked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'purple_dragon').mkdir()
            (root / 'purple_dragon/__init__.py').write_text('__version__ = "0.3.1"\n')
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args])
            git('init', '-q')
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
            (root / 'private.txt').write_text('must not ship')
            windows = root / 'dist'
            (windows / '_internal').mkdir(parents=True)
            (windows / 'PurpleDragonFlipperStudio.exe').write_bytes(b'fixture')
            (windows / '_internal/support.txt').write_text('support')
            previous = module.ROOT
            module.ROOT = root
            try:
                out = root / 'release'
                module.package(out, windows)
                manifest = json.loads((out / 'release-manifest.json').read_text())
                self.assertEqual(manifest['commit'], git('rev-parse', 'HEAD').decode().strip())
                for name, digest in manifest['assets'].items():
                    self.assertEqual(digest, hashlib.sha256((out / name).read_bytes()).hexdigest())
                    with zipfile.ZipFile(out / name) as archive:
                        self.assertFalse(any('private.txt' in n for n in archive.namelist()))
                        if 'Windows' in name:
                            self.assertIn('PurpleDragonFlipperStudio/_internal/support.txt', archive.namelist())
                (root / 'purple_dragon/__init__.py').write_text('__version__ = "9.9.9"\n')
                with self.assertRaisesRegex(RuntimeError, 'Commit tracked changes'):
                    module.package(out, windows)
            finally:
                module.ROOT = previous
