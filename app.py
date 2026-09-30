"""Run the desktop GUI; screenshot options are for local visual verification."""
import argparse
import sys
from pathlib import Path
from PySide6.QtCore import QTimer, QSettings
from PySide6.QtWidgets import QApplication
from purple_dragon.window import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--screenshot', type=Path)
    parser.add_argument('--size', default=None)
    parser.add_argument('--isolated-settings', type=Path)
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName('Purple Dragon Flipper Studio')
    settings = QSettings(str(args.isolated_settings), QSettings.Format.IniFormat) if args.isolated_settings else None
    window = MainWindow(settings=settings)
    if args.size:
        width, height = map(int, args.size.lower().split('x'))
        window.resize(width, height)
    window.show()
    if args.screenshot:
        def capture():
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            if not window.grab().save(str(args.screenshot)):
                raise RuntimeError('Screenshot could not be saved.')
            window.close()
            app.quit()
        QTimer.singleShot(700, capture)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
