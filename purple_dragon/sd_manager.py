"""SD browser UI; all protocol and disk work stays in the serial worker."""
from pathlib import Path, PurePosixPath
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QHBoxLayout,
                               QFileDialog, QInputDialog, QMessageBox, QProgressBar, QHeaderView)
from .neon import panel, button
from .sd_protocol import child_path, sd_path
from .backup_center import BackupCenterMixin


class SDManagerMixin(BackupCenterMixin):
    def build_sd_manager(self, lay):
        self.sd_busy = False
        self.sd_last_error = ''
        self.sd_available = False
        self.sd_directory = '/ext'
        box, layout = panel('SD File Manager')
        hint = QLabel('Identify the Flipper in CLI mode, then Refresh / Probe SD. Transfers are limited to 4 MiB. Uploads never overwrite existing remote files.')
        hint.setWordWrap(True); layout.addWidget(hint)
        self.sd_path_field = QLineEdit('/ext'); self.sd_path_field.setReadOnly(True)
        self.sd_path_field.setAccessibleName('Current SD directory'); layout.addWidget(self.sd_path_field)
        navigation = QHBoxLayout()
        self.sd_root_btn = button('SD root', lambda: self.start_sd_operation('list', '/ext'))
        self.sd_up_btn = button('Up', self.sd_up)
        self.sd_refresh_btn = button('Refresh / Probe SD', lambda: self.start_sd_operation('list', self.sd_directory))
        for item in (self.sd_root_btn, self.sd_up_btn, self.sd_refresh_btn): navigation.addWidget(item)
        layout.addLayout(navigation)
        self.sd_tree = QTreeWidget(); self.sd_tree.setHeaderLabels(['Name', 'Type', 'Bytes'])
        self.sd_tree.setRootIsDecorated(False); self.sd_tree.setMinimumHeight(180)
        self.sd_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2): self.sd_tree.header().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.sd_tree.setAccessibleName('SD directory entries')
        self.sd_tree.itemDoubleClicked.connect(self.sd_open_directory)
        self.sd_tree.itemSelectionChanged.connect(self.update_sd_controls)
        layout.addWidget(self.sd_tree)
        actions = QHBoxLayout()
        self.sd_upload_btn = button('Upload', self.sd_upload)
        self.sd_download_btn = button('Download', self.sd_download)
        self.sd_mkdir_btn = button('New folder', self.sd_new_folder)
        self.sd_delete_btn = button('Delete', self.sd_delete)
        for item in (self.sd_upload_btn, self.sd_download_btn, self.sd_mkdir_btn, self.sd_delete_btn): actions.addWidget(item)
        layout.addLayout(actions)
        self.sd_progress = QProgressBar(); self.sd_progress.setRange(0, 100); self.sd_progress.setValue(0)
        layout.addWidget(self.sd_progress)
        self.sd_cancel_btn = button('Cancel & disconnect', self.sd_cancel)
        layout.addWidget(self.sd_cancel_btn)
        self.sd_status = QLabel('SD availability has not been checked.'); self.sd_status.setWordWrap(True)
        self.sd_status.setTextFormat(Qt.TextFormat.PlainText); self.sd_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.sd_status)
        self.sd_delete_btn.setToolTip('Delete one selected file or empty folder after confirmation. No recursive deletion or root deletion.')
        self.sd_upload_btn.setToolTip('Uploads to a new name using a staged file and integrity checks. Existing remote files are never overwritten.')
        self.sd_download_btn.setToolTip('Downloads binary data, verifies MD5, then replaces the chosen local destination atomically.')
        self.sd_tree.setToolTip('Double-click a folder to enter it. Select a file for Download or Delete.')
        lay.addWidget(box)
        self.update_sd_controls()

    def sd_ready(self):
        return self.connected and self.session is not None and self.mode.currentText() == 'CLI' and self.device_adapter.state == 'identified' and not self.last_connection_error and not self.connection_cancelled and not self.connection_lost

    def update_sd_controls(self):
        ready = self.sd_ready() and not self.sd_busy
        selected = self.sd_tree.currentItem()
        entry = selected.data(0, Qt.ItemDataRole.UserRole) if selected else None
        for control in (self.sd_root_btn, self.sd_refresh_btn): control.setEnabled(bool(ready))
        self.sd_up_btn.setEnabled(bool(ready and self.sd_directory != '/ext'))
        self.sd_tree.setEnabled(bool(ready and self.sd_available))
        for control in (self.sd_upload_btn, self.sd_mkdir_btn): control.setEnabled(bool(ready and self.sd_available))
        self.sd_delete_btn.setEnabled(bool(ready and self.sd_available and entry))
        self.sd_download_btn.setEnabled(bool(ready and self.sd_available and entry and not entry['directory']))
        self.sd_cancel_btn.setEnabled(bool(self.sd_busy))
        self.update_backup_controls()
        self.update_ir_controls()
        self.update_gpio_controls()

    def reset_sd_manager(self):
        if not hasattr(self, 'sd_tree'): return
        self.sd_busy = self.sd_available = False
        self.sd_tree.clear(); self.sd_directory = '/ext'; self.sd_path_field.setText('/ext')
        self.sd_progress.setValue(0)
        self.reset_backup_center()
        self.sd_status.setText((self.sd_last_error + ' Reconnect and identify before retrying.') if self.sd_last_error else 'SD availability has not been checked. Identify the device and probe again.')
        self.update_sd_controls()

    def start_sd_operation(self, operation, path, local=None):
        if not self.sd_ready() or self.sd_busy or (operation != 'list' and not self.sd_available): return
        try:
            sd_path(path, operation in ('list','backup','restore_preview','restore'))
            if not self.session.request_storage(operation, path, local):
                self.sd_status.setText('Serial queue is busy. Let commands finish, then retry.'); return
        except ValueError as exc:
            self.sd_status.setText(str(exc)); return
        self.sd_last_error = ''
        self.sd_busy = True
        self.identify_btn.setEnabled(False); self.send_btn.setEnabled(False)
        self.sd_status.setText('Working… Cancel disconnects to reset the CLI safely. A failed upload may leave a staged .part file.')
        self.sd_progress.setValue(0)
        if operation == 'list': self.sd_tree.clear()
        self.update_sd_controls()

    def sd_operation_finished(self, session, result):
        if result.get('operation') in ('gpio_probe','gpio_action'):
            self.gpio_operation_finished(session,result)
            return
        if result.get('operation') in ('ir_probe','ir_transmit'):
            self.ir_operation_finished(session,result)
            return
        if result.get('operation') in ('backup','restore_preview','restore'):
            self.backup_operation_finished(session, result)
            return
        if session is self.session and not result.get('ok') and self.connection_cancelled:
            self.sd_last_error = result.get('error', 'Operation cancelled.')
            self.sd_status.setText(self.sd_last_error)
            return
        if session is not self.session or not self.sd_busy or not self.sd_ready(): return
        self.sd_busy = False
        if result.get('ok'):
            self.sd_progress.setValue(100)
            self.sd_status.setText('Complete.' + (' SHA-256: ' + result['sha256'] if result.get('sha256') else ''))
            if result['operation'] == 'list':
                self.sd_available = True
                self.sd_directory = result['path']; self.sd_path_field.setText(self.sd_directory)
                self.device_adapter.capabilities = self.device_adapter.capabilities | {'sd_files'}
                self.sd_tree.clear()
                for entry in sorted(result['entries'], key=lambda e: (not e['directory'], e['name'].casefold())):
                    item = QTreeWidgetItem([entry['name'], 'Folder' if entry['directory'] else 'File', '' if entry['directory'] else str(entry['size'])])
                    item.setData(0, Qt.ItemDataRole.UserRole, entry); item.setToolTip(0, entry['name']); self.sd_tree.addTopLevelItem(item)
                self.sd_status.setText(str(len(result['entries'])) + ' entries · SD storage responded.')
            self.send_btn.setEnabled(True); self.identify_btn.setEnabled(True)
            self.update_sd_controls()
            if result['operation'] in ('mkdir', 'remove', 'upload'):
                self.start_sd_operation('list', self.sd_directory)
        else:
            self.sd_available = False; self.sd_tree.clear()
            self.device_adapter.capabilities = self.device_adapter.capabilities - {'sd_files'}
            self.sd_last_error = result.get('error', 'Storage operation failed.')
            self.sd_status.setText(self.sd_last_error + ' Reconnect and identify before retrying.')
            # The worker closes this session after any storage failure to avoid binary/text desynchronization.
            self.send_btn.setEnabled(False); self.identify_btn.setEnabled(False)
            self.update_sd_controls()
            self.log('SD operation failed; reconnect required.', 'Warning')

    def sd_progress_update(self, session, done, total):
        if session is self.session and self.sd_busy:
            self.sd_progress.setValue(int(done * 100 / total) if total else 100)
            self.backup_progress.setValue(int(done * 100 / total) if total else 100)

    def sd_up(self):
        if self.sd_directory != '/ext': self.start_sd_operation('list', str(PurePosixPath(self.sd_directory).parent))

    def sd_open_directory(self, item, *_):
        entry = item.data(0, Qt.ItemDataRole.UserRole)
        if entry and entry['directory']: self.start_sd_operation('list', child_path(self.sd_directory, entry['name']))

    def sd_selected(self):
        item = self.sd_tree.currentItem()
        return item.data(0, Qt.ItemDataRole.UserRole) if item else None

    def sd_download(self):
        entry = self.sd_selected()
        if not entry or entry['directory']: return
        destination, _ = QFileDialog.getSaveFileName(self, 'Download SD file', entry['name'], 'All files (*)')
        if destination: self.start_sd_operation('download', child_path(self.sd_directory, entry['name']), destination)

    def sd_upload(self):
        source, _ = QFileDialog.getOpenFileName(self, 'Upload file to SD', '', 'All files (*)')
        if not source: return
        name, ok = QInputDialog.getText(self, 'Upload to new remote file', 'New file name (no overwrite):', text=Path(source).name)
        if ok:
            try: self.start_sd_operation('upload', child_path(self.sd_directory, name), source)
            except ValueError as exc: self.sd_status.setText(str(exc))

    def sd_new_folder(self):
        name, ok = QInputDialog.getText(self, 'New SD folder', 'Folder name:')
        if ok:
            try: self.start_sd_operation('mkdir', child_path(self.sd_directory, name))
            except ValueError as exc: self.sd_status.setText(str(exc))

    def sd_delete(self):
        entry = self.sd_selected()
        if not entry: return
        remote = child_path(self.sd_directory, entry['name'])
        if QMessageBox.question(self, 'Delete from SD', 'Delete ' + remote + '?\nOnly files and empty folders can be removed. This cannot be undone.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.start_sd_operation('remove', remote)

    def sd_cancel(self):
        if self.sd_busy and self.session is not None: self.toggle_connection()
