# Dependency notices

PurpleDragonFlipperStudio project code is MIT licensed; see LICENSE. Dependencies retain their own copyright and license terms. The Windows package keeps its Qt/Python runtime in _internal; distribute the entire folder and preserve bundled notices.

| Component | Release build | Upstream source / notices |
| --- | --- | --- |
| CPython | Python 3.12 series in Windows CI; exact runtime in diagnostics | https://github.com/python/cpython/tree/3.12 · licenses/Python-3.12-LICENSE.txt (3.12.12 reference text) |
| PySide6, Shiboken6 and Qt | PySide6 6.10.2 | https://github.com/pyside/pyside-setup/tree/v6.10.2 · https://code.qt.io/cgit/qt/ · licenses/LGPL-3.0-only.txt and GPL-3.0-only.txt |
| pyserial | 3.5 | https://github.com/pyserial/pyserial/tree/v3.5 · licenses/pyserial-LICENSE.txt |
| PyInstaller bootloader/build tooling | 6.16.0 | https://github.com/pyinstaller/pyinstaller/tree/v6.16.0 · licenses/PyInstaller-COPYING.txt |

PySide6's installed metadata declares LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only; this distribution uses the LGPL option for the dynamically loaded Qt/PySide runtime. Preserve library replacement and reverse-engineering rights provided by the applicable license. The build specification and pinned requirements are included in the source ZIP for rebuilding; no project restriction is imposed on replacing those shared libraries. Qt's bundled third-party components have their own notices in the upstream Qt source and runtime distribution.

The copyright notices in the copied license texts belong to their respective authors. These notices do not relicense the app under a dependency's license. Flipper Devices trademarks and referenced websites belong to their owners; this is an independent project.
