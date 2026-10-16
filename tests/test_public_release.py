import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import Mock, patch
from test_release_packaging import module as package_module


def load_script(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/'scripts'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
verify_module=load_script('verify_release');smoke_module=load_script('smoke_windows')

class PublicReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for name,text in {'purple_dragon/__init__.py':'__version__ = "1.0.0"\n','LICENSE':'MIT fixture','docs/QUICKSTART.md':'Quick start fixture','docs/DEPENDENCIES.md':'Dependency notices fixture','docs/RELEASE-v1.0.0.md':'Release notes fixture','scripts/verify_release.py':'fixture'}.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        self.git('init','-q');self.git('add','.');self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','release fixture')
        self.commit=self.git('rev-parse','HEAD').decode().strip();self.windows=self.root/'dist';(self.windows/'_internal').mkdir(parents=True)
        (self.windows/'PurpleDragonFlipperStudio.exe').write_bytes(b'synthetic executable');(self.windows/'_internal/runtime.dll').write_bytes(b'synthetic runtime')
        self.output=self.root/'release';self.old_root=package_module.ROOT;package_module.ROOT=self.root;self.addCleanup(setattr,package_module,'ROOT',self.old_root)
        package_module.package(self.output,self.windows)
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.root),*args])
    def verify(self,**kwargs):return verify_module.verify(self.output,**kwargs)
    def rewrite_archive(self,name,transform):
        path=self.output/name
        with zipfile.ZipFile(path) as archive:entries={n:archive.read(n) for n in archive.namelist()};comment=archive.comment
        transform(entries)
        with zipfile.ZipFile(path,'w') as archive:
            archive.comment=comment
            for key,value in entries.items():archive.writestr(key,value)
        manifest=json.loads((self.output/'release-manifest.json').read_text());manifest['assets'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
        (self.output/'release-manifest.json').write_text(json.dumps(manifest));(self.output/'SHA256SUMS.txt').write_text(''.join(digest+'  '+key+'\n' for key,digest in manifest['assets'].items()))
    def test_round_trip_requires_both_archives_and_matching_commit(self):
        report=self.verify(expected_commit=self.commit,require_windows=True);self.assertEqual(report['version'],'1.0.0');self.assertEqual(len(report['verified_assets']),2)
    def test_windows_bundle_contains_public_docs_and_metadata(self):
        with zipfile.ZipFile(self.output/'PurpleDragonFlipperStudio-v1.0.0-Windows-x64.zip') as archive:
            for name in ['README-FIRST.txt','LICENSE.txt','DEPENDENCIES.md','RELEASE-NOTES.md','release-info.json']:self.assertIn('PurpleDragonFlipperStudio/'+name,archive.namelist())
    def test_modified_archive_fails_hash_check(self):
        with (self.output/'PurpleDragonFlipperStudio-v1.0.0-Windows-x64.zip').open('ab') as stream:stream.write(b'tampered')
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):self.verify()
    def test_expected_commit_and_checksum_list_mismatches_fail(self):
        with self.assertRaisesRegex(ValueError,'expected commit'):self.verify(expected_commit='0'*40)
        (self.output/'SHA256SUMS.txt').write_text('')
        with self.assertRaisesRegex(ValueError,'differs'):self.verify()
    def test_unsafe_archive_path_rejected_even_with_updated_digest(self):
        for bad in ['../outside','/absolute','PurpleDragonFlipperStudio/../outside','PurpleDragonFlipperStudio/./dot','PurpleDragonFlipperStudio\\bad']:
            def add(entries):entries[bad]=b'bad'
            self.rewrite_archive('PurpleDragonFlipperStudio-v1.0.0-Windows-x64.zip',add)
            with self.assertRaisesRegex(ValueError,'Unsafe'):self.verify()
            self.rewrite_archive('PurpleDragonFlipperStudio-v1.0.0-Windows-x64.zip',lambda entries:entries.pop(bad))
    def test_wrong_windows_commit_metadata_rejected(self):
        self.rewrite_archive('PurpleDragonFlipperStudio-v1.0.0-Windows-x64.zip',lambda entries:entries.update({'PurpleDragonFlipperStudio/release-info.json':json.dumps({'version':'1.0.0','commit':'0'*40}).encode()}))
        with self.assertRaisesRegex(ValueError,'metadata differs'):self.verify()
    def test_source_commit_comment_and_version_checked(self):
        name='PurpleDragonFlipperStudio-v1.0.0-Source.zip'
        self.rewrite_archive(name,lambda entries:entries.update({'PurpleDragonFlipperStudio-v1.0.0/purple_dragon/__init__.py':b'__version__ = "9.0.0"'}))
        with self.assertRaisesRegex(ValueError,'Source version'):self.verify()
        self.rewrite_archive(name,lambda entries:entries.update({'PurpleDragonFlipperStudio-v1.0.0/purple_dragon/__init__.py':b'__version__ = "1.0.0"'}))
        with zipfile.ZipFile(self.output/name,'a') as archive:archive.comment=b'0'*40
        self.rewrite_archive(name,lambda entries:None)
        with self.assertRaisesRegex(ValueError,'Source archive commit'):self.verify()
    def test_incomplete_windows_layout_rejected(self):
        self.rewrite_archive('PurpleDragonFlipperStudio-v1.0.0-Windows-x64.zip',lambda entries:entries.pop('PurpleDragonFlipperStudio/_internal/runtime.dll'))
        with self.assertRaisesRegex(ValueError,'layout is incomplete'):self.verify()
    def test_manifest_cannot_request_arbitrary_file(self):
        path=self.output/'release-manifest.json';manifest=json.loads(path.read_text());manifest['assets']['../secret']='0'*64;path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'unexpected'):self.verify()
    def test_missing_windows_build_rejected_before_source_is_written(self):
        new=self.root/'new-release'
        with self.assertRaises(RuntimeError):package_module.package(new,self.root/'missing')
        self.assertFalse(new.exists())
    def test_source_only_package_supported_but_not_windows_gate(self):
        new=self.root/'source-only';package_module.package(new)
        self.assertEqual(len(verify_module.verify(new)['verified_assets']),1)
        with self.assertRaisesRegex(ValueError,'Missing'):verify_module.verify(new,require_windows=True)
    def test_smoke_launch_uses_isolated_settings_and_requires_image(self):
        executable=self.windows/'PurpleDragonFlipperStudio.exe'
        def render(command,**kwargs):
            import struct
            self.assertIn('--isolated-settings',command);self.assertEqual(kwargs['timeout'],45)
            Path(command[command.index('--screenshot')+1]).write_bytes(b'\x89PNG\r\n\x1a\n'+b'\x00'*8+struct.pack('>II',1280,850))
        with patch.object(smoke_module.subprocess,'run',side_effect=render):smoke_module.smoke(executable)
        with patch.object(smoke_module.subprocess,'run'):
            with self.assertRaises(FileNotFoundError):smoke_module.smoke(executable)
