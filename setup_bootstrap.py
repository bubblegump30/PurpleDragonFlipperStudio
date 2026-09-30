"""Select Python before setup; preserve incompatible environments."""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBE = (
    "import json,sys,struct,platform,sysconfig; "
    "print(json.dumps({'version':list(sys.version_info[:2]),"
    "'bits':struct.calcsize('P')*8,'implementation':platform.python_implementation(),"
    "'free_threaded':bool(sysconfig.get_config_var('Py_GIL_DISABLED'))}))"
)


def supported(info):
    try:
        return (3, 10) <= tuple(info['version']) <= (3, 14) and info['bits'] == 64 and info['implementation'] == 'CPython' and not info.get('free_threaded', False)
    except (KeyError, TypeError):
        return False


def probe(command):
    try:
        result = subprocess.run(command + ['-c', PROBE], capture_output=True, text=True, timeout=15)
        if result.returncode:
            return None
        info = json.loads(result.stdout.strip())
        return info if supported(info) else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def candidates():
    commands = []
    if shutil.which('py'):
        for version in ['3.14', '3.13', '3.12', '3.11', '3.10']:
            commands.append(['py', '-' + version])
    commands.append([sys.executable])
    for name in ['python', 'python3']:
        executable = shutil.which(name)
        if executable:
            commands.append([executable])
    return commands


def choose_interpreter(commands, check=probe):
    for command in commands:
        info = check(command)
        if info is not None:
            return command, info
    return None, None


def environment_python(root):
    return root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def prepare_environment(root, commands=None, check=probe, run=subprocess.run):
    executable = environment_python(root)
    existing = check([str(executable)]) if executable.exists() else None
    if existing is not None:
        print('Using existing Python {}.{} (64-bit).'.format(*existing['version']))
        return executable
    command, info = choose_interpreter(candidates() if commands is None else commands, check)
    if command is None:
        raise RuntimeError('No compatible Python found. Install standard 64-bit Python 3.10-3.14 from https://www.python.org/downloads/windows/ and rerun Setup.bat. Python 3.12 is a good choice. Enable the Python launcher during installation.')
    print('Selected Python {}.{} (64-bit): {}'.format(*info['version'], ' '.join(command)))
    env = root / '.venv'
    if env.exists():
        backup = root / ('.venv.previous-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        env.rename(backup)
        print('Preserved incompatible environment as ' + backup.name)
    result = run(command + ['-m', 'venv', str(env)], cwd=str(root))
    if result.returncode or not executable.exists():
        raise RuntimeError('Virtual environment creation failed. Review the Python error above.')
    if check([str(executable)]) is None:
        raise RuntimeError('Created environment failed its compatibility check.')
    return executable


def main():
    try:
        executable = prepare_environment(ROOT)
        result = subprocess.run([str(executable), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], cwd=str(ROOT))
        if result.returncode:
            raise RuntimeError('Dependency installation failed. Check the pip message above and your internet connection.')
        result = subprocess.run([str(executable), '-c', 'import PySide6, serial; print("GUI dependencies verified.")'], cwd=str(ROOT))
        if result.returncode:
            raise RuntimeError('Dependency import verification failed.')
        print('Setup complete. Open Start.bat to launch Purple Dragon.')
        return 0
    except (OSError, RuntimeError) as exc:
        print('Setup failed: ' + str(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
