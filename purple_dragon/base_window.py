import json
import os
import platform
import sys
import tempfile
import PySide6
import serial
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QUrl, QTimer, QEvent
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap, QTextCursor, QColor, QTextDocument
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QStackedWidget, QScrollArea, QComboBox, QLineEdit,
    QPlainTextEdit, QCheckBox, QSlider, QFileDialog, QMessageBox,
    QGraphicsDropShadowEffect, QButtonGroup, QApplication,
)
from .backend import SerialSession, HardwareAdapter, discover_ports
from .matrix import MatrixRain
from .ir_files import inspect_ir
from .theme import THEMES, stylesheet
from . import __version__
from .neon import button, panel

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
WEBSITE = 'https://www.purpledragonfoundationltd.xyz/'


def label(text, role=None):
    item = QLabel(text)
    if role:
        item.setObjectName(role)
    item.setWordWrap(True)
    return item






class WorkspaceServices(QMainWindow):





    def build_console(self, lay):
        box, b = panel('Serial console')
        b.addWidget(label('Incoming serial text appears here. Send transmits your text exactly with the selected line ending. No commands are sent automatically.', 'muted'))
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.document().setMaximumBlockCount(2000)
        self.console.setMinimumHeight(300)
        self.console.setPlaceholderText('Waiting for serial data…')
        b.addWidget(self.console)
        row = QHBoxLayout()
        self.command = QLineEdit()
        self.command.setPlaceholderText('Enter serial text or a CLI command…')
        self.command.setMaxLength(1024)
        self.command_history = []
        self.history_position = 0
        self.history_draft = ''
        self.command.installEventFilter(self)
        self.command.setToolTip('Up/Down recalls commands sent during this session; recall never transmits.')
        self.command.returnPressed.connect(self.send_command)
        self.ending = QComboBox()
        self.ending.addItems(['CRLF', 'LF', 'None'])
        self.ending.setCurrentText(str(self.settings.value('line_ending', 'CRLF')))
        self.ending.currentTextChanged.connect(lambda value: self.settings.setValue('line_ending', value))
        self.send_btn = button('Send  →', self.send_command, True)
        self.send_btn.setEnabled(False)
        row.addWidget(self.command, 1)
        row.addWidget(self.ending)
        row.addWidget(self.send_btn)
        b.addLayout(row)
        utility = QHBoxLayout()
        utility.addWidget(button('Clear console', self.console.clear))
        utility.addWidget(button('Export transcript', self.export_console))
        self.console_scroll = QCheckBox('Auto scroll')
        self.console_scroll.setChecked(self.settings.value('console_scroll', True, type=bool))
        self.console_scroll.toggled.connect(lambda value: self.settings.setValue('console_scroll', value))
        utility.addWidget(self.console_scroll)
        utility.addWidget(button('Clear command history', self.clear_command_history))
        utility.addStretch()
        b.addLayout(utility)
        search_row = QHBoxLayout()
        self.console_search = QLineEdit()
        self.console_search.setPlaceholderText('Find text in transcript…')
        self.console_search.setMaxLength(256)
        self.console_search.returnPressed.connect(self.find_console)
        search_row.addWidget(self.console_search, 1)
        search_row.addWidget(button('Previous', lambda: self.find_console(True)))
        search_row.addWidget(button('Next', self.find_console))
        self.search_feedback = label('', 'muted')
        search_row.addWidget(self.search_feedback)
        b.addLayout(search_row)
        lay.addWidget(box)

    def build_device(self, lay):
        box, b = panel('Detected device')
        self.device_details = label('Connect a serial port to view its available metadata.', 'muted')
        self.device_details.setTextFormat(Qt.TextFormat.PlainText)
        self.device_details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        b.addWidget(self.device_details)
        b.addWidget(label('Battery, firmware, SD storage and device name require the device protocol adapter. Values will appear only after successful queries.', 'muted'))
        lay.addWidget(box)

    def build_ir(self, lay):
        box, b = panel('IR Remote Studio  /  Local file preview')
        b.addWidget(label('Open a local Flipper .ir file to inspect it. Transmission requires integration with your existing IR backend.', 'muted'))
        b.addWidget(button('Open .ir file', self.open_ir, True))
        self.ir_entries=[]
        self.ir_filter=QLineEdit();self.ir_filter.setPlaceholderText('Filter signal names…');self.ir_filter.setMaxLength(256)
        self.ir_signals=QComboBox();self.ir_signals.setMinimumWidth(150)
        row=QHBoxLayout();row.addWidget(self.ir_filter,1);row.addWidget(self.ir_signals,1);b.addLayout(row)
        self.ir_summary=label('No file loaded.','muted');self.ir_summary.setTextFormat(Qt.TextFormat.PlainText);b.addWidget(self.ir_summary)
        self.ir_filter.textChanged.connect(self.filter_ir_signals)
        self.ir_signals.currentIndexChanged.connect(self.select_ir_signal)
        self.ir_preview = QPlainTextEdit()
        self.ir_preview.setReadOnly(True)
        self.ir_preview.setMinimumHeight(300)
        self.ir_preview.setPlaceholderText('No infrared file selected.')
        b.addWidget(self.ir_preview)
        b.addWidget(button('Copy file text', lambda: QApplication.clipboard().setText(self.ir_preview.toPlainText())))
        transmit = button('Transmit signal', lambda: None)
        transmit.setToolTip('Requires the RC7 IR transmission backend.')
        transmit.setEnabled(False)
        b.addWidget(transmit)
        lay.addWidget(box)

    def build_tools(self, lay):
        box, b = panel('Workspace tools')
        b.addWidget(label('Export the local information you have collected in this GUI.', 'muted'))
        b.addWidget(button('Export console transcript', self.export_console))
        b.addWidget(button('Export saved GPIO setups', self.export_profiles))
        b.addWidget(button('Import GPIO setups', self.import_profiles))
        b.addWidget(button('Export settings backup', self.export_settings_backup))
        b.addWidget(button('Restore settings backup', self.import_settings_backup))
        b.addWidget(label('Settings backups contain local presets, appearance, console preferences and the selected workspace. Restore replaces those settings after validation and confirmation.', 'muted'))
        b.addWidget(button('Export session log', self.export_log))
        b.addWidget(button('Export diagnostic report', self.export_diagnostics))
        b.addWidget(button('Help Center · F1', self.beginner_guide))
        backup = button('Back up Flipper SD card', lambda: None)
        backup.setToolTip('Requires the RC7 device backup backend.')
        backup.setEnabled(False)
        b.addWidget(backup)
        b.addWidget(label('Device backup, restore and firmware operations await the RC7 backend. Setup import/export handles only local JSON notes.', 'muted'))
        lay.addWidget(box)

    def build_apps(self, lay):
        for title, text, url in [
            ('Official Flipper Apps', 'Browse the official catalog. App installation is managed by the official service.', 'https://lab.flipper.net/apps'),
            ('NFC App Catalog', 'Explore the official NFC app category.', 'https://lab.flipper.net/apps/category/nfc'),
            ('Flipper Zero Awesome', 'Open the community resource directory.', 'https://123fzero.github.io/flipper-zero-awesome/'),
            ('Purple Dragon Foundation', 'Projects, software and music from Kyle Austin Hillier.', WEBSITE),
        ]:
            box, b = panel(title)
            b.addWidget(label(text, 'muted'))
            b.addWidget(button('Open in browser  ↗', lambda checked=False, u=url: self.open_url(u)))
            lay.addWidget(box)

    def build_log(self, lay):
        box, b = panel('Live session log')
        self.log_entries = []
        filters = QHBoxLayout()
        self.log_search = QLineEdit();self.log_search.setPlaceholderText('Filter activity text…');self.log_search.setMaxLength(256)
        self.log_level = QComboBox();self.log_level.addItems(['All', 'Info', 'Warning', 'Error'])
        filters.addWidget(self.log_search, 1);filters.addWidget(self.log_level)
        b.addLayout(filters)
        self.log_search.textChanged.connect(self.render_log)
        self.log_level.currentTextChanged.connect(self.render_log)
        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.document().setMaximumBlockCount(1000)
        self.logs.setMinimumHeight(360)
        b.addWidget(self.logs)
        row = QHBoxLayout()
        row.addWidget(button('Export log', self.export_log))
        row.addWidget(button('Export visible', self.export_visible_log))
        row.addWidget(button('Copy visible', self.copy_visible_log))
        row.addWidget(button('Clear log', self.clear_log))
        self.log_scroll = QCheckBox('Auto scroll');self.log_scroll.setChecked(True);row.addWidget(self.log_scroll)
        row.addStretch()
        b.addLayout(row)
        self.log_count = label('', 'muted');b.addWidget(self.log_count)
        lay.addWidget(box)

    def build_appearance(self, lay):
        box, b = panel('Make it yours')
        b.addWidget(label('COLOR PALETTE', 'eyebrow'))
        self.theme = QComboBox()
        self.theme.addItems(THEMES)
        self.theme.setCurrentText(self.settings.value('theme', 'Neo Purple'))
        b.addWidget(self.theme)
        self.animation = QCheckBox('Live Matrix background')
        self.animation.setChecked(self.settings.value('matrix', True, type=bool))
        self.glow = QCheckBox('Button glow')
        self.glow.setChecked(self.settings.value('glow', True, type=bool))
        self.reduced = QCheckBox('Reduced motion / power saving')
        self.reduced.setChecked(self.settings.value('reduced', False, type=bool))
        for control in [self.animation, self.glow, self.reduced]:
            b.addWidget(control)
        self.intensity = QSlider(Qt.Orientation.Horizontal)
        self.intensity.setRange(5, 90)
        self.intensity.setValue(self.settings.value('intensity', 32, type=int))
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(10, 150)
        self.speed.setValue(self.settings.value('speed', 55, type=int))
        b.addWidget(label('MATRIX BRIGHTNESS', 'eyebrow'))
        b.addWidget(self.intensity)
        b.addWidget(label('RAIN SPEED', 'eyebrow'))
        b.addWidget(self.speed)
        b.addWidget(label('Your appearance settings persist between launches. Matrix animation pauses while minimized.', 'muted'))
        b.addWidget(button('Restore default appearance', self.reset_appearance))
        self.theme.currentTextChanged.connect(self.apply_theme)
        for control in [self.animation, self.glow, self.reduced]:
            control.toggled.connect(self.apply_theme)
        self.intensity.valueChanged.connect(self.apply_theme)
        self.speed.valueChanged.connect(self.apply_theme)
        lay.addWidget(box)




    def connection_feedback(self, message):
        self.connection_message.setText(message)
        self.connection_message.setToolTip(message)

    def save_port_preferences(self, *_):
        port = self.port.currentData()
        if port and self.session is None:
            self.settings.setValue('ports/' + port + '/mode', self.mode.currentText())
            self.settings.setValue('ports/' + port + '/baud', self.baud.currentText())

    def port_selected(self, *_):
        if self.session is not None:
            return
        port = self.port.currentData()
        for control, key in [(self.mode, 'mode'), (self.baud, 'baud')]:
            value = str(self.settings.value('ports/' + str(port) + '/' + key,
                                          self.settings.value(key, 'CLI' if key == 'mode' else '230400')))
            control.blockSignals(True)
            control.setCurrentIndex(max(0, control.findText(value)))
            control.blockSignals(False)
        info = self.port_info.get(port)
        details = ['Selected port: ' + str(port)] if port else ['No serial ports detected.']
        if info:
            details += ['Description: ' + str(info.description),
                        'Manufacturer: ' + str(info.manufacturer or 'Unavailable'),
                        'USB serial: ' + str(info.serial_number or 'Unavailable')]
        self.device_details.setText('\n'.join(details) + '\nDevice identity has not been verified.')
        self.port.setToolTip('\n'.join(details))
        self.connect_btn.setEnabled(bool(port))

    def refresh_ports(self):
        if self.session is not None:
            return
        selected = self.port.currentData() or self.settings.value('port', '')
        self.port.blockSignals(True)
        self.port.clear()
        self.port_info = {}
        try:
            ports = discover_ports()
        except Exception as exc:
            self.port.addItem('Discovery failed', None)
            self.port.blockSignals(False)
            self.port_selected()
            self.badge.setText('○  DISCOVERY ERROR')
            self.connection_feedback('Port discovery failed: ' + str(exc) + '. Check USB and refresh.')
            self.log('Port discovery failed: ' + str(exc), 'Error')
            return
        self.port_info = {p.device: p for p in ports}
        for p in ports:
            self.port.addItem(f'{p.device} · {p.description}', p.device)
        if not ports:
            self.port.addItem('No ports', None)
        idx = self.port.findData(selected)
        if idx >= 0:
            self.port.setCurrentIndex(idx)
        self.port.blockSignals(False)
        self.port_selected()
        self.badge.setText('○  DISCONNECTED')
        if selected and idx < 0:
            self.connection_feedback(f'Saved port {selected} is unavailable. Select a detected port or refresh.')
        else:
            self.connection_feedback('Select a port and connect.' if ports else 'Connect your device by USB, close other serial tools, then refresh.')

    def serial_fault(self, message):
        self.last_connection_error = message
        self.send_btn.setEnabled(False)
        self.log('Serial error: ' + message, 'Error')
        self.connection_feedback('Serial error: ' + message + '. Close other serial tools, check USB, refresh and retry.')

    def toggle_connection(self):
        if self.session is not None:
            self.connection_cancelled = True
            self.send_btn.setEnabled(False)
            self.badge.setText('○  DISCONNECTING')
            self.connection_feedback('Closing serial transport…')
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText('Disconnecting…')
            self.session.requestInterruption()
            return
        port = self.port.currentData()
        if not port:
            return
        self.last_connection_error = None
        self.connection_cancelled = False
        self.save_port_preferences()
        self.settings.setValue('port', port)
        self.settings.setValue('mode', self.mode.currentText())
        self.settings.setValue('baud', self.baud.currentText())
        self.session = SerialSession(port, int(self.baud.currentText()), self)
        self.session.opened.connect(self.serial_opened)
        self.session.received.connect(self.receive)
        self.session.fault.connect(self.serial_fault)
        self.session.finished.connect(self.serial_finished)
        self.connect_btn.setText('Cancel connection')
        for control in [self.port, self.mode, self.baud, self.refresh_btn]:
            control.setEnabled(False)
        self.badge.setText('○  CONNECTING')
        self.connection_feedback('Opening ' + port + '…')
        self.session.start()

    def serial_opened(self):
        if self.connection_cancelled:
            return
        self.connected = True
        self.badge.setText('●  SERIAL CONNECTED')
        self.connect_btn.setText('Disconnect')
        self.send_btn.setEnabled(True)
        self.metrics['CONNECTION'].setText(self.port.currentData())
        self.metrics['WORKSPACE'].setText(self.mode.currentText())
        self.connection_feedback('Serial transport open. Device identity and protocol are not yet verified.')
        info = self.port_info.get(self.port.currentData())
        details = [f'Port: {self.port.currentData()}', f'Baud: {self.baud.currentText()}', f'Mode: {self.mode.currentText()}']
        if info:
            details += [f'Description: {info.description}', f'Manufacturer: {info.manufacturer or "Unavailable"}', f'USB serial: {info.serial_number or "Unavailable"}']
        self.device_details.setText('\n'.join(details))
        self.log('Serial transport connected: ' + self.port.currentData())

    def serial_finished(self):
        session, self.session = self.session, None
        if session:
            session.deleteLater()
        self.connected = False
        self.badge.setText('●  DISCONNECTED')
        self.connect_btn.setText('Retry' if self.last_connection_error else 'Connect')
        self.connect_btn.setEnabled(bool(self.port.currentData()))
        self.send_btn.setEnabled(False)
        for control in [self.port, self.mode, self.baud, self.refresh_btn]:
            control.setEnabled(True)
        self.metrics['CONNECTION'].setText('Offline')
        self.device_details.setText('Disconnected. Reconnect to view current port metadata.')
        if self.last_connection_error:
            self.badge.setText('○  CONNECTION ERROR')
            self.connection_feedback('Serial error: ' + self.last_connection_error + '. Close other serial tools, check USB, refresh and retry.')
        else:
            self.connection_feedback('Disconnected. Select a port to reconnect.')
        self.log('Serial transport closed.')

    def eventFilter(self, watched, event):
        if watched is getattr(self, 'command', None) and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down) and event.modifiers() == Qt.KeyboardModifier.NoModifier:
                if self.command_history:
                    if self.history_position == len(self.command_history):
                        self.history_draft = self.command.text()
                    offset = -1 if event.key() == Qt.Key.Key_Up else 1
                    self.history_position = max(0, min(len(self.command_history), self.history_position + offset))
                    self.command.setText(self.command_history[self.history_position] if self.history_position < len(self.command_history) else self.history_draft)
                return True
        return super().eventFilter(watched, event)

    def clear_command_history(self):
        self.command_history.clear()
        self.history_position = 0
        self.history_draft = ''

    def find_console(self, backward=False):
        query = self.console_search.text()
        if not query:
            self.search_feedback.setText('Enter search text')
            return
        flags = QTextDocument.FindFlag.FindBackward if backward else QTextDocument.FindFlag(0)
        found = self.console.find(query, flags)
        if not found:
            cursor = self.console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start)
            self.console.setTextCursor(cursor)
            found = self.console.find(query, flags)
        self.search_feedback.setText('Match' if found else 'No match')

    def receive(self, text):
        scrollbar = self.console.verticalScrollBar()
        old_position = scrollbar.value()
        selection = self.console.textCursor()
        cursor = QTextCursor(self.console.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if self.console.document().characterCount() > 250000:
            self.console.setPlainText(self.console.toPlainText()[-180000:])
        if self.console_scroll.isChecked():
            self.console.setTextCursor(cursor)
            self.console.ensureCursorVisible()
        else:
            self.console.setTextCursor(selection)
            scrollbar.setValue(old_position)

    def send_command(self):
        if not self.connected or self.session is None:
            return
        text = self.command.text()
        if not text:
            return
        ending = {'CRLF':'\r\n', 'LF':'\n', 'None':''}[self.ending.currentText()]
        if self.session.send(text + ending):
            self.log(f'Transmit queued: {len((text + ending).encode("utf-8"))} bytes')
            if not self.command_history or self.command_history[-1] != text:
                self.command_history.append(text)
                self.command_history = self.command_history[-100:]
            self.history_position = len(self.command_history)
            self.history_draft = ''
            self.command.clear()
        else:
            self.log('Send queue full. Wait for the device to consume queued data.', 'Warning')

    def profiles(self):
        try:
            data = json.loads(self.settings.value('profiles', '{}'))
            return self.validate_profiles(data)
        except (ValueError, TypeError):
            return {}

    @staticmethod
    def validate_profiles(data):
        if not isinstance(data, dict) or len(data) > 200:
            raise ValueError('Expected an object containing up to 200 setups.')
        for name, entry in data.items():
            if not isinstance(name, str) or not name.strip() or len(name) > 120:
                raise ValueError('Invalid setup name.')
            if not isinstance(entry, dict) or not isinstance(entry.get('pin'), str) or not isinstance(entry.get('notes'), str) or len(entry['notes']) > 100000:
                raise ValueError('Each setup must contain text pin and notes fields.')
        return data

    def refresh_profiles(self, selected=None):
        self.profile.blockSignals(True)
        self.profile.clear()
        self.profile.addItem('New setup', None)
        for name in sorted(self.profiles()):
            self.profile.addItem(name, name)
        idx = self.profile.findData(selected)
        self.profile.setCurrentIndex(max(0, idx))
        self.profile.blockSignals(False)
        self.load_profile()

    def load_profile(self, *_):
        name = self.profile.currentData()
        entry = self.profiles().get(name)
        self.profile_name.setText(name or '')
        self.notes.setPlainText(entry['notes'] if entry else '')
        if entry and self.pin.findText(entry['pin']) >= 0:
            self.pin.setCurrentText(entry['pin'])

    def new_profile(self):
        self.refresh_profiles()
        self.profile_name.setFocus()
        self.profile_feedback.setText('New local setup · Enter a name, choose a pin and save.')

    def duplicate_profile(self):
        data = self.profiles()
        original = self.profile.currentData()
        if original not in data:
            self.profile_feedback.setText('Select a saved setup to duplicate.')
            return
        if len(data) >= 200:
            self.notify('Setup limit', 'Delete a setup before adding another; the limit is 200.')
            return
        stem = original[:100] + ' copy'
        name = stem
        index = 2
        while name in data:
            name = stem + ' ' + str(index)
            index += 1
        data[name] = dict(data[original])
        self.settings.setValue('profiles', json.dumps(data))
        self.refresh_profiles(name)
        self.profile_feedback.setText('Duplicated: ' + name)
        self.log('Duplicated local setup: ' + name)

    def rename_profile(self):
        original = self.profile.currentData()
        name = self.profile_name.text().strip()
        data = self.profiles()
        if original not in data:
            self.profile_feedback.setText('Select a saved setup, then enter its new name.')
            return
        if not name or len(name) > 120:
            self.notify('Setup name', 'Enter a setup name of 1–120 characters.')
            return
        if name == original:
            self.profile_feedback.setText('The setup already has this name.')
            return
        if name in data:
            self.notify('Name already used', 'Choose a unique name to rename this setup.')
            return
        data[name] = data.pop(original)
        self.settings.setValue('profiles', json.dumps(data))
        self.refresh_profiles(name)
        self.profile_feedback.setText('Renamed: ' + name)
        self.log('Renamed local setup: ' + original + ' → ' + name)

    def save_profile(self):
        if self.profile_store_error():
            self.notify('Saved setups need recovery', 'The saved preset store is invalid. Restore a valid settings backup before saving; existing data has been preserved.')
            return
        name = self.profile_name.text().strip()
        if not name or len(name) > 120:
            self.notify('Setup name', 'Enter a setup name of 1–120 characters.')
            return
        data = self.profiles()
        if name in data and name != self.profile.currentData():
            if QMessageBox.question(self, 'Replace setup', f'Replace saved setup "{name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
        data[name] = {'pin': self.pin.currentText(), 'notes': self.notes.toPlainText()}
        try:
            self.validate_profiles(data)
        except ValueError as exc:
            self.notify('Setup could not be saved', str(exc))
            return
        self.settings.setValue('profiles', json.dumps(data))
        self.refresh_profiles(name)
        self.log('Saved setup: ' + name)
        self.profile_feedback.setText('Saved locally: ' + name)

    def delete_profile(self):
        name = self.profile.currentData()
        if not name:
            return
        if QMessageBox.question(self, 'Delete setup', f'Delete local setup "{name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        data = self.profiles()
        data.pop(name, None)
        self.settings.setValue('profiles', json.dumps(data))
        self.refresh_profiles()
        self.log('Deleted local setup: ' + name)

    def gpio_action(self, action):
        # A future controller must check connection, pin mode and output arming.
        self.notify('Backend integration', 'Wire the RC7 GPIO controller before enabling these actions.')

    @staticmethod
    def atomic_write_text(path, content):
        target = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                             prefix='.purple-dragon-', suffix='.tmp', delete=False) as output:
                temporary = Path(output.name)
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def profile_store_error(self):
        try:
            self.validate_profiles(json.loads(self.settings.value('profiles', '{}')))
        except (ValueError, TypeError) as exc:
            return str(exc)
        return None

    def diagnostics(self):
        error = self.profile_store_error()
        return {
            'application': 'Purple Dragon Flipper GUI', 'version': __version__,
            'created_by': 'KyleAustin85', 'generated_at': datetime.now().astimezone().isoformat(),
            'runtime': {'python': platform.python_version(), 'platform': sys.platform,
                        'pyside6': PySide6.__version__, 'pyserial': serial.__version__},
            'workspace': self.workspace.currentText(), 'theme': self.theme.currentText(),
            'connection': {'state': 'connected' if self.connected else ('opening_or_closing' if self.session else 'disconnected'),
                           'detected_port_count': len(self.port_info), 'last_error_present': bool(self.last_connection_error)},
            'settings': {'status': self.settings.status().name, 'preset_store_valid': error is None,
                         'preset_count': len(self.profiles()) if error is None else None},
            'buffers': {'retained_log_entries': len(self.log_entries), 'command_history_entries': len(self.command_history)},
            'device_backend': {'capabilities': sorted(self.adapter.capabilities)},
            'verification': 'Windows packaging and physical hardware checks require local verification.'}

    def export_diagnostics(self):
        self.export_text(json.dumps(self.diagnostics(), indent=2), 'Export diagnostic report',
                         'purple-dragon-diagnostics.json', 'JSON (*.json)')

    def export_text(self, content, title, default, file_filter):
        path, _ = QFileDialog.getSaveFileName(self, title, default, file_filter)
        if path:
            try:
                self.atomic_write_text(path, content)
                self.log('Export saved: ' + Path(path).name)
            except OSError as exc:
                self.notify('Export failed', str(exc))

    def export_console(self):
        self.export_text(self.console.toPlainText(), 'Export console', 'console-transcript.txt', 'Text files (*.txt)')

    def export_log(self):
        self.export_text('\n'.join(entry[1] for entry in self.log_entries), 'Export session log', 'purple-dragon-session.txt', 'Text files (*.txt)')

    def settings_backup(self):
        return {'format': 'purple-dragon-settings', 'schema': 1, 'version': __version__,
                'profiles': self.profiles(), 'preferences': {
                    'theme': self.theme.currentText(), 'matrix': self.animation.isChecked(),
                    'glow': self.glow.isChecked(), 'reduced': self.reduced.isChecked(),
                    'intensity': self.intensity.value(), 'speed': self.speed.value(),
                    'line_ending': self.ending.currentText(), 'console_scroll': self.console_scroll.isChecked(),
                    'last_workspace': self.workspace.currentText()}}

    def validate_settings_backup(self, data):
        if not isinstance(data, dict) or data.get('format') != 'purple-dragon-settings' or type(data.get('schema')) is not int or data['schema'] != 1:
            raise ValueError('Unsupported settings backup format or schema.')
        self.validate_profiles(data.get('profiles'))
        prefs = data.get('preferences')
        expected = {'theme', 'matrix', 'glow', 'reduced', 'intensity', 'speed', 'line_ending', 'console_scroll', 'last_workspace'}
        if not isinstance(prefs, dict) or set(prefs) != expected:
            raise ValueError('Missing or unknown preference fields.')
        for key in ['matrix', 'glow', 'reduced', 'console_scroll']:
            if type(prefs[key]) is not bool:
                raise ValueError('Invalid boolean preference: ' + key)
        for key, low, high in [('intensity', 5, 90), ('speed', 10, 150)]:
            if type(prefs[key]) is not int or not low <= prefs[key] <= high:
                raise ValueError('Invalid preference range: ' + key)
        for key, choices in [('theme', THEMES), ('line_ending', ['CRLF', 'LF', 'None']), ('last_workspace', self.pages)]:
            if not isinstance(prefs[key], str) or prefs[key] not in choices:
                raise ValueError('Unsupported preference: ' + key)
        return data

    def restore_settings_backup(self, data):
        self.validate_settings_backup(data)
        prefs = data['preferences']
        self.settings.setValue('profiles', json.dumps(data['profiles']))
        controls = [(self.theme, 'theme'), (self.animation, 'matrix'), (self.glow, 'glow'),
                    (self.reduced, 'reduced'), (self.intensity, 'intensity'), (self.speed, 'speed'),
                    (self.ending, 'line_ending'), (self.console_scroll, 'console_scroll')]
        for control, key in controls:
            control.blockSignals(True)
            if isinstance(control, QComboBox): control.setCurrentText(prefs[key])
            elif isinstance(control, QCheckBox): control.setChecked(prefs[key])
            else: control.setValue(prefs[key])
            control.blockSignals(False)
            self.settings.setValue(key, prefs[key])
        self.refresh_profiles()
        self.apply_theme()
        self.navigate(prefs['last_workspace'])
        self.settings.sync()
        self.log('Restored local settings and presets from backup.')

    def export_settings_backup(self):
        if self.profile_store_error():
            self.notify('Saved setups need recovery', 'The preset store is invalid. Restore a valid backup before exporting settings; existing data has been preserved.')
            return
        content = json.dumps(self.settings_backup(), indent=2)
        if len(content.encode('utf-8')) > 5_000_000:
            self.notify('Backup too large', 'Settings backups are limited to 5 MB. Reduce preset notes or export GPIO setups separately.')
            return
        self.export_text(content, 'Export settings backup', 'purple-dragon-settings.json', 'JSON (*.json)')

    def import_settings_backup(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Restore settings backup', '', 'JSON (*.json)')
        if not path: return
        try:
            if Path(path).stat().st_size > 5_000_000:
                raise ValueError('Settings backup exceeds the 5 MB limit.')
            data = self.validate_settings_backup(json.loads(Path(path).read_text(encoding='utf-8')))
            summary = f'Replace local presets with {len(data["profiles"])} saved setups and restore appearance, console preferences and workspace?'
            if QMessageBox.question(self, 'Restore settings backup', summary, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            self.restore_settings_backup(data)
        except (OSError, ValueError, TypeError) as exc:
            self.notify('Restore failed', str(exc))

    def export_profiles(self):
        self.export_text(json.dumps(self.profiles(), indent=2), 'Export setups', 'gpio-setups.json', 'JSON (*.json)')

    def import_profiles(self):
        if self.profile_store_error():
            self.notify('Saved setups need recovery', 'Restore a valid settings backup before importing; existing data has been preserved.')
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Import GPIO setups', '', 'JSON (*.json)')
        if not path:
            return
        try:
            if Path(path).stat().st_size > 2_000_000:
                raise ValueError('Setup file must be smaller than 2 MB.')
            data = self.validate_profiles(json.loads(Path(path).read_text(encoding='utf-8')))
            existing = self.profiles()
            conflicts = set(existing).intersection(data)
            if conflicts:
                response = QMessageBox.question(self, 'Replace matching setups?', f'{len(conflicts)} setup names already exist. Replace matching entries?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if response != QMessageBox.StandardButton.Yes:
                    return
            existing.update(data)
            self.validate_profiles(existing)
            self.settings.setValue('profiles', json.dumps(existing))
            self.refresh_profiles()
            self.log(f'Imported {len(data)} local setups.')
        except (ValueError, OSError, UnicodeError) as exc:
            self.notify('Import failed', str(exc))

    def open_ir(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open infrared file', '', 'Flipper infrared (*.ir);;Text files (*.txt)')
        if not path:
            return
        try:
            if Path(path).stat().st_size > 1_000_000:
                raise ValueError('Preview files must be smaller than 1 MB.')
            text=Path(path).read_text(encoding='utf-8-sig')
            entries,warnings=inspect_ir(text)
            self.ir_preview.setPlainText(text)
            self.ir_entries=entries
            self.filter_ir_signals()
            self.ir_summary.setText(f'{Path(path).name} · {len(entries)} signals · {len(warnings)} structure warnings. These checks do not verify device compatibility.')
            self.ir_summary.setToolTip('\n'.join(warnings[:50]) if warnings else 'Basic structure checks passed; payload values are not validated.')
            self.log('Previewing infrared file: ' + Path(path).name)
        except (ValueError, OSError, UnicodeError) as exc:
            self.notify('Preview failed', str(exc))

    def filter_ir_signals(self, *_):
        self.ir_signals.blockSignals(True)
        self.ir_signals.clear()
        query=self.ir_filter.text().casefold()
        for entry in self.ir_entries:
            if query in entry['name'].casefold():
                self.ir_signals.addItem(entry['name'] or '(unnamed)', entry['line'])
        self.ir_signals.blockSignals(False)
        self.select_ir_signal()

    def select_ir_signal(self, *_):
        line=self.ir_signals.currentData()
        if line is None: return
        cursor=QTextCursor(self.ir_preview.document().findBlockByNumber(line))
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        self.ir_preview.setTextCursor(cursor)
        self.ir_preview.ensureCursorVisible()

    def render_log(self, *_):
        query = self.log_search.text().casefold()
        level = self.log_level.currentText()
        visible = [text for severity, text in self.log_entries
                   if (level == 'All' or severity == level) and query in text.casefold()]
        position = self.logs.verticalScrollBar().value()
        self.logs.setPlainText('\n'.join(visible))
        if self.log_scroll.isChecked():
            self.logs.moveCursor(QTextCursor.MoveOperation.End)
        else:
            self.logs.verticalScrollBar().setValue(position)
        self.log_count.setText(f'{len(visible)} visible / {len(self.log_entries)} retained · Limit: 1000 entries')

    def clear_log(self):
        self.log_entries.clear()
        self.render_log()

    def copy_visible_log(self):
        QApplication.clipboard().setText(self.logs.toPlainText())

    def export_visible_log(self):
        self.export_text(self.logs.toPlainText(), 'Export visible log', 'purple-dragon-filtered-log.txt', 'Text files (*.txt)')

    def log(self, message, level='Info'):
        level = level if level in ('Info', 'Warning', 'Error') else 'Info'
        stamp = datetime.now().strftime('%H:%M:%S')
        self.log_entries.append((level, f'[{stamp}] [{level.upper()}] {message}'))
        self.log_entries = self.log_entries[-1000:]
        self.render_log()
        self.activity.setText('LATEST ACTIVITY  /  ' + message)
        self.statusBar().showMessage(message)

    def notify(self, title, message):
        QMessageBox.information(self, title, message)

    def beginner_guide(self):
        from .help_center import HelpCenter
        if not hasattr(self, 'help_center'):
            self.help_center = HelpCenter(self)
        self.help_center.show()
        self.help_center.raise_()
        self.help_center.activateWindow()

    def open_url(self, url):
        if not QDesktopServices.openUrl(QUrl(url)):
            self.notify('Browser', 'Unable to open the browser. Address: ' + url)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'rain'):
            self.rain.setGeometry(self.shell.rect())
            self.rain.lower()

    def showEvent(self, event):
        super().showEvent(event)
        self.rain.setGeometry(self.shell.rect())
        self.rain.lower()
        self.rain.set_running(not self.isMinimized())

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, 'rain'):
            self.rain.set_running(not self.isMinimized() and self.isVisible())

    def closeEvent(self, event):
        if self.session is not None:
            self.session.requestInterruption()
            if not self.session.wait(1600):
                event.ignore()
                self.connection_message.setText('Waiting for the serial worker to finish. Close again shortly.')
                return
        self.settings.sync()
        self.rain.timer.stop()
        event.accept()
