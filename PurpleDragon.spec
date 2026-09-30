from pathlib import Path

project = Path(SPECPATH)
a = Analysis(
    [str(project / 'app.py')],
    pathex=[str(project)],
    binaries=[],
    datas=[(str(project / 'assets'), 'assets')],
    hiddenimports=['serial.tools.list_ports_windows'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
    name='PurpleDragonFlipperStudio', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False, icon=str(project / 'assets' / 'dragon.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PurpleDragonFlipperStudio')
