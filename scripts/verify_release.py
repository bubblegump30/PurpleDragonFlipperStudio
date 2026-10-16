"""Verify release hashes, archive structure and commit metadata without extracting or running code."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile


def read_json(path):
    if path.stat().st_size>65536:raise ValueError('Manifest exceeds 64 KiB.')
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict):raise ValueError('Manifest must be an object.')
    return data


def verify(folder, expected_commit=None, require_windows=False):
    manifest=read_json(folder/'release-manifest.json')
    version=manifest.get('version');commit=manifest.get('commit');assets=manifest.get('assets')
    if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid release version.')
    if not isinstance(commit,str) or not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('Invalid commit metadata.')
    if expected_commit is not None and commit!=expected_commit:raise ValueError('Release commit does not match expected commit.')
    prefix='PurpleDragonFlipperStudio-v'+version
    source=prefix+'-Source.zip';windows=prefix+'-Windows-x64.zip'
    allowed={source,windows}
    if not isinstance(assets,dict) or source not in assets or not set(assets)<=allowed or (require_windows and windows not in assets):raise ValueError('Missing or unexpected release assets.')
    if (folder/'SHA256SUMS.txt').stat().st_size>2048:raise ValueError('Checksum file exceeds its limit.')
    checksums=(folder/'SHA256SUMS.txt').read_text(encoding='utf-8')
    if len(checksums)>2048:raise ValueError('Invalid checksum file.')
    lines={}
    for line in checksums.splitlines():
        match=re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9.-]+)',line)
        if not match or match[2] in lines:raise ValueError('Invalid or duplicate checksum entry.')
        lines[match[2]]=match[1]
    if lines!=assets:raise ValueError('Checksum list differs from release manifest.')
    for name,digest in assets.items():
        if not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):raise ValueError('Invalid archive digest.')
        path=folder/name
        if path.stat().st_size>1024**3:raise ValueError('Archive exceeds 1 GiB.')
        digest_hash=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest_hash.update(block)
        actual=digest_hash.hexdigest()
        if actual!=digest:raise ValueError('Archive checksum mismatch: '+name)
        with zipfile.ZipFile(path) as archive:
            entries=archive.infolist()
            if len(entries)>10000 or sum(x.file_size for x in entries)>2*1024**3:raise ValueError('Archive exceeds verification limits.')
            seen=set()
            for entry in entries:
                raw_name=entry.orig_filename
                parts=raw_name.rstrip('/').split('/')
                if not parts or any(not p for p in parts) or raw_name.startswith('/') or any(p in ('.','..') for p in parts) or any(c in raw_name for c in ('\\',':')) or any(ord(c)<32 for c in raw_name) or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Unsafe archive path.')
                if entry.filename.casefold() in seen:raise ValueError('Duplicate archive path.')
                seen.add(entry.filename.casefold())
            if archive.testzip() is not None:raise ValueError('Corrupt archive payload.')
            names=set(archive.namelist())
            if name==source:
                root=prefix+'/'
                required={root+'purple_dragon/__init__.py',root+'LICENSE',root+'docs/QUICKSTART.md',root+'scripts/verify_release.py'}
                if not required<=names or any(not n.startswith(root) for n in names):raise ValueError('Source archive layout is incomplete.')
                if archive.comment.decode('ascii')!=commit:raise ValueError('Source archive commit differs from manifest.')
                if archive.getinfo(root+'purple_dragon/__init__.py').file_size>4096:raise ValueError('Source version file is oversized.')
                text=archive.read(root+'purple_dragon/__init__.py').decode('utf-8')
                if '__version__ = "'+version+'"' not in text:raise ValueError('Source version differs from manifest.')
            else:
                root='PurpleDragonFlipperStudio/'
                required={root+x for x in ('PurpleDragonFlipperStudio.exe','README-FIRST.txt','LICENSE.txt','DEPENDENCIES.md','RELEASE-NOTES.md','release-info.json')}
                if not required<=names or not any(n.startswith(root+'_internal/') and not n.endswith('/') for n in names) or any(not n.startswith(root) for n in names):raise ValueError('Windows archive layout is incomplete.')
                if archive.getinfo(root+'PurpleDragonFlipperStudio.exe').file_size==0:raise ValueError('Windows executable is empty.')
                if archive.getinfo(root+'release-info.json').file_size>4096:raise ValueError('Build metadata is oversized.')
                info=json.loads(archive.read(root+'release-info.json'))
                if info!={'version':version,'commit':commit}:raise ValueError('Windows package metadata differs from manifest.')
    return {'version':version,'commit':commit,'verified_assets':list(assets)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('--expected-commit');parser.add_argument('--require-windows',action='store_true')
    args=parser.parse_args();print(json.dumps(verify(args.folder,args.expected_commit,args.require_windows)))
