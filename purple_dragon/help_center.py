"""Searchable local help with no network or hardware side effects."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QComboBox,QLineEdit,QPlainTextEdit,QLabel
from . import __version__

TOPICS = {
    'Getting started': 'Extract the source ZIP into a new folder. On Windows run Setup.bat, then Start.bat. Setup supports standard 64-bit CPython 3.10–3.14. Debug-Launch.bat keeps launch errors visible.\n\nConnect the device by USB, close other serial tools, refresh ports and select the correct port. Connect opens only the serial transport; it does not verify Flipper identity. CLI and UART Bridge use different device configurations. No device commands are sent automatically.',
    'Keyboard shortcuts': 'F1: Help Center\nF5: Refresh ports while disconnected\nCtrl+Home: Home / GPIO Lab\nCtrl+L: UART Console input\nCtrl+,: Appearance\nAlt+Left / Alt+Right: Back / Forward\nCtrl+1..8: Workspace tabs from left to right\n\nIn command input, Up/Down recalls successfully queued commands. Down past the newest restores your draft. Press Enter or Send to transmit; recall never transmits.',
    'Console and logs': 'UART Console supports explicit text sends with CRLF, LF or no line ending. Command history holds 100 entries in memory. Transcript search wraps through matches; turn Auto scroll off to read older text.\n\nLive Log combines case-insensitive text and severity filters. Export log includes all retained entries; Export visible and Copy visible include the filtered view. Clear log removes all retained entries. Up to 1000 entries are kept during this session.',
    'Presets and backups': 'GPIO presets store pin selection and notes locally. New clears the editor; Duplicate copies saved fields to a unique name. To Rename, select a saved preset and type a unique new name. Save Setup stores current editor contents.\n\nBackup & Tools exports/restores settings backups up to 5 MB. Restore replaces saved presets and included preferences after validation and confirmation. Export a current backup before restoring for rollback. Connections, transcripts and command history are excluded.',
    'IR file inspection': 'Open a local .ir file up to 1 MB. Filter signal names and select a signal to jump to its line. Hover the summary for basic structure warnings. Copy file text copies the whole preview.\n\nStructure checks do not validate payload values or hardware compatibility. Transmission requires the RC7 backend and remains disabled.',
    'Troubleshooting': 'No ports: check the USB data cable, device, drivers and Refresh.\nPort busy or connection error: close qFlipper and other serial programs, check USB, then Retry. Full error text is available on hover and in Live Log.\nCorrupt preset store: existing data is preserved. Restore a valid settings backup before saving or importing presets.\nExport failed: verify destination access and free space. Existing destination files are preserved if replacement fails.\nUse Export diagnostic report in Backup & Tools for application/runtime versions and settings health without notes, serial text or raw error strings.',
    'Release and capabilities': 'v0.3.1 updates release instructions, creator credit, and packaging with matching source and Windows archives plus SHA-256 checksums.\n\nAvailable: serial transport, local presets, appearance, navigation memory, console tools, logs, IR file inspection, settings backups and diagnostics.\n\nGPIO hardware reads/writes, IR transmission, SD backup, app installation and telemetry require RC7 integration. Windows packaging was verified for v0.3.0. Physical hardware integration remains unverified.\n\nBuild-Windows.bat produces dist/PurpleDragonFlipperStudio/PurpleDragonFlipperStudio.exe. Distribute the entire folder including _internal. The source ZIP contains no prebuilt Windows executable.'}

class HelpCenter(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('Purple Dragon Help Center · '+__version__)
        self.setObjectName('helpCenter')
        self.setStyleSheet('QDialog#helpCenter { background: #060b18; }')
        self.resize(780,580)
        layout=QVBoxLayout(self)
        row=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText('Search all help topics…');self.search.setMaxLength(256)
        self.topic=QComboBox();self.topic.addItems(TOPICS);row.addWidget(self.search,1);row.addWidget(self.topic);layout.addLayout(row)
        self.text=QPlainTextEdit();self.text.setReadOnly(True);layout.addWidget(self.text)
        self.feedback=QLabel();layout.addWidget(self.feedback)
        self.search.textChanged.connect(self.render);self.topic.currentTextChanged.connect(self.render);self.render()
    def render(self,*_):
        query=self.search.text().strip().casefold()
        if query:
            matches=[name+'\n\n'+body for name,body in TOPICS.items() if query in (name+' '+body).casefold()]
            self.text.setPlainText('\n\n────────\n\n'.join(matches) if matches else 'No matching topics. Try a different search term.')
            self.feedback.setText(f'{len(matches)} matching topics');self.topic.setEnabled(False)
        else:
            self.topic.setEnabled(True);name=self.topic.currentText();self.text.setPlainText(name+'\n\n'+TOPICS[name]);self.feedback.setText('F1 opens this guide · Created by KyleAustin85')
