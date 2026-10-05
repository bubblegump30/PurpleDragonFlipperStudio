"""Package source and a Windows build from one clean Git commit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def package(output, windows=None):
    if git('status', '--porcelain', '--untracked-files=no').strip():
        raise RuntimeError('Commit tracked changes before packaging.')
    version = re.search(r'__version__ = "([0-9.]+)"', (ROOT / 'purple_dragon/__init__.py').read_text()).group(1)
    commit = git('rev-parse', 'HEAD').decode().strip()
    output.mkdir(parents=True, exist_ok=True)
    prefix = 'PurpleDragonFlipperStudio-v' + version
    source = output / (prefix + '-Source.zip')
    subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=zip', '--prefix=' + prefix + '/', '-o', str(source.resolve()), commit], check=True)
    archives = [source]
    if windows:
        if not (windows / 'PurpleDragonFlipperStudio.exe').is_file() or not (windows / '_internal').is_dir():
            raise RuntimeError('Windows build must include the executable and _internal folder.')
        archive = output / (prefix + '-Windows-x64.zip')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in sorted(windows.rglob('*')):
                if path.is_file():
                    z.write(path, Path('PurpleDragonFlipperStudio') / path.relative_to(windows))
        archives.append(archive)
    hashes = {}
    for path in archives:
        with path.open('rb') as stream:
            hashes[path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    (output / 'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name, h in hashes.items()), encoding='utf-8')
    (output / 'release-manifest.json').write_text(json.dumps({'version': version, 'commit': commit, 'assets': hashes}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'version': version, 'commit': commit, 'assets': list(hashes)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'release-assets')
    parser.add_argument('--windows', type=Path)
    args = parser.parse_args()
    package(args.output, args.windows)
