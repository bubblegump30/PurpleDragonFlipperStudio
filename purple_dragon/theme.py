from pathlib import Path
ASSETS=Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    'Neo Purple': '#b500ff', 'Matrix Green': '#45dc8d',
    'Electric Cyan': '#48d7f0', 'Dragon Ember': '#ff9a55',
    'Crimson': '#ff6684', 'Sakura Pink': '#ee85d4',
    'Royal Blue': '#759aff', 'Solar Gold': '#edc768',
}


def stylesheet(accent):
    return """
    QWidget { color:#e3e6ff; font-family:'Segoe UI'; font-size:12px; }
    QMainWindow, QWidget#content { background:transparent; }
    QFrame#sidebar { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(3,12,25,247),stop:1 rgba(4,7,19,240)); border-right:1px solid #233752; }
    QFrame#neonPanel, QFrame#connectionPanel { background:transparent; border:none; }
    QLabel { background:transparent; border:none; }
    QLabel#title { font-size:26px; font-weight:700; color:#ede3ff; }
    QLabel#sectionTitle { font-size:14px; font-weight:600; color:#ece4ff; }
    QLabel#muted { color:#a5b5d9; font-size:11px; }
    QLabel#eyebrow { color:ACCENT; font-size:11px; font-weight:700; }
    QLabel#connectionStatus { color:#d9d0ff; font-size:12px; }
    QLineEdit, QComboBox, QPlainTextEdit { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #020812,stop:1 #060f1c); border:1px solid #3b547a; border-radius:5px; padding:7px 10px; color:#e3edff; selection-background-color:ACCENT; min-height:20px; }
    QComboBox { padding-right:23px; }
    QComboBox::drop-down { border-left:1px solid #293b59; width:22px; }
    QComboBox::down-arrow { image:url("CHEVRON"); width:14px; height:14px; }
    QComboBox QAbstractItemView { background:#081327; color:#e3edff; selection-background-color:#422563; }
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus { border:1px solid ACCENT; }
    QPlainTextEdit { font-family:'Consolas'; font-size:11px; }
    QPlainTextEdit#gpioResponse { color:#8dff91; }
    QCheckBox { spacing:8px; color:#d3dff6; font-size:11px; }
    QCheckBox::indicator { width:17px; height:17px; border:1px solid #4a6697; background:#040b17; border-radius:3px; }
    QCheckBox::indicator:checked { background:ACCENT; border:1px solid #efacff; image:url("CHECK"); }
    QCheckBox:disabled { color:#a8b3c9; }
    QSlider::groove:horizontal { height:5px; background:#173750; }
    QSlider::sub-page:horizontal { background:ACCENT; }
    QSlider::handle:horizontal { background:ACCENT; width:17px; margin:-6px 0; border-radius:8px; }
    QScrollArea { background:transparent; border:none; }
    QScrollBar:vertical { background:#020712; width:6px; margin:0; }
    QScrollBar::handle:vertical { background:#52326b; border-radius:3px; min-height:25px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
    QStatusBar { background:#030813; border-top:1px solid #293552; font-size:10px; color:#9baecf; }
    QFrame#separator { background:#30405c; }
    QSplitter::handle { background:#20344c; border:1px solid #31577a; border-radius:3px; }
    QSplitter::handle:hover { background:ACCENT; }
    QToolTip { background:#091327; border:1px solid ACCENT; color:#eee6ff; padding:8px; }
    QMessageBox,QDialog { background:#061022; }
    QMessageBox QPushButton { background:#30214a; border:1px solid ACCENT; padding:8px 20px; border-radius:5px; }
    """.replace('ACCENT',accent).replace('CHEVRON',(ASSETS/'chevron.svg').as_posix()).replace('CHECK',(ASSETS/'check.svg').as_posix())
