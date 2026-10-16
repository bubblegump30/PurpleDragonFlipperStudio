"""Backup/restore UI; previews and payload verification run in the serial worker."""
from datetime import datetime
from PySide6.QtWidgets import QLabel, QLineEdit, QPlainTextEdit, QHBoxLayout, QFileDialog, QMessageBox, QProgressBar
from PySide6.QtCore import Qt
from .neon import panel, button
from .sd_protocol import child_path


class BackupCenterMixin:
    def build_backup_center(self, lay):
        self.backup_plan = None; self.backup_last_error = ''
        box, layout = panel('SD Backup & Restore Center')
        self.backup_source_label = QLabel('Identify the device and probe SD Files first.')
        self.backup_source_label.setWordWrap(True); layout.addWidget(self.backup_source_label)
        hint = QLabel('Limits: 4 MiB/file · 256 MiB/backup · 2,000 entries. Nothing is skipped. Restore creates a NEW SD folder; it never merges, overwrites, or formats.')
        hint.setWordWrap(True); layout.addWidget(hint)
        row = QHBoxLayout()
        self.backup_all_btn = button('Back up /ext', lambda: self.choose_backup_destination('/ext'))
        self.backup_folder_btn = button('Back up current folder', lambda: self.choose_backup_destination(self.sd_directory))
        row.addWidget(self.backup_all_btn); row.addWidget(self.backup_folder_btn); layout.addLayout(row)
        self.restore_folder = QLineEdit(); self.restore_folder.setReadOnly(True)
        self.restore_folder.setPlaceholderText('Choose a completed backup folder containing manifest.json…')
        self.restore_folder.setAccessibleName('Backup folder to restore'); layout.addWidget(self.restore_folder)
        self.restore_choose_btn = button('Choose backup folder', self.choose_restore_folder); layout.addWidget(self.restore_choose_btn)
        self.restore_target = QLineEdit('Restored-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
        self.restore_target.setMaxLength(120); self.restore_target.setAccessibleName('New restore folder name')
        self.restore_target.setToolTip('A new direct child of /ext. Existing remote folders are refused.')
        layout.addWidget(QLabel('New folder name under /ext:')); layout.addWidget(self.restore_target)
        self.restore_target.textChanged.connect(self.invalidate_restore_preview)
        row = QHBoxLayout()
        self.restore_preview_btn = button('Verify & preview', self.preview_restore)
        self.restore_confirm_btn = button('Restore previewed files', self.confirm_restore, True)
        row.addWidget(self.restore_preview_btn); row.addWidget(self.restore_confirm_btn); layout.addLayout(row)
        self.backup_preview = QPlainTextEdit(); self.backup_preview.setReadOnly(True); self.backup_preview.setMinimumHeight(160)
        self.backup_preview.setPlaceholderText('Preview validates the manifest and every payload checksum, checks the target, and lists paths before any remote write.')
        self.backup_preview.setAccessibleName('Restore preview'); layout.addWidget(self.backup_preview)
        self.backup_progress = QProgressBar(); self.backup_progress.setRange(0,100); layout.addWidget(self.backup_progress)
        self.backup_cancel_btn = button('Cancel & disconnect', self.sd_cancel); layout.addWidget(self.backup_cancel_btn)
        self.backup_status = QLabel('Identify the device, then Refresh / Probe SD in SD Files.')
        self.backup_status.setWordWrap(True); self.backup_status.setTextFormat(Qt.TextFormat.PlainText)
        self.backup_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); layout.addWidget(self.backup_status)
        for widget in (self.backup_all_btn,self.backup_folder_btn,self.restore_preview_btn,self.restore_confirm_btn,self.backup_cancel_btn): widget.setEnabled(False)
        lay.addWidget(box)

    def update_backup_controls(self):
        if not hasattr(self, 'backup_all_btn'): return
        ready = self.sd_ready() and self.sd_available and not self.sd_busy
        self.backup_source_label.setText('Current SD folder: ' + self.sd_directory)
        for widget in (self.backup_all_btn,self.backup_folder_btn): widget.setEnabled(bool(ready))
        self.restore_choose_btn.setEnabled(not self.sd_busy); self.restore_target.setEnabled(not self.sd_busy)
        self.restore_preview_btn.setEnabled(bool(ready and self.restore_folder.text()))
        self.restore_confirm_btn.setEnabled(bool(ready and self.backup_plan))
        self.backup_cancel_btn.setEnabled(bool(self.sd_busy))

    def reset_backup_center(self):
        if not hasattr(self, 'backup_all_btn'): return
        self.backup_plan = None; self.backup_preview.clear(); self.backup_progress.setValue(0)
        self.backup_status.setText(self.backup_last_error or 'Identify the device and probe SD Files before backup or restore.')

    def invalidate_restore_preview(self, *_):
        self.backup_plan = None
        self.backup_preview.clear()
        if hasattr(self, 'sd_tree'): self.update_backup_controls()

    def choose_backup_destination(self, source):
        parent = QFileDialog.getExistingDirectory(self, 'Choose parent folder for a NEW verified backup')
        if parent: self.start_backup_job('backup', source, parent)

    def choose_restore_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose completed Purple Dragon SD backup folder')
        if folder:
            self.restore_folder.setText(folder); self.invalidate_restore_preview()

    def start_backup_job(self, operation, path, local):
        if not self.sd_ready() or not self.sd_available or self.sd_busy: return
        self.backup_last_error = ''; self.backup_plan = None
        self.backup_status.setText('Working… Preflight, verification and file transfer share one worker. Cancel disconnects safely.')
        self.backup_progress.setValue(0)
        self.start_sd_operation(operation, path, local)
        self.update_backup_controls()

    def preview_restore(self):
        try: target = child_path('/ext', self.restore_target.text())
        except ValueError as exc: self.backup_status.setText(str(exc)); return
        self.start_backup_job('restore_preview', '/ext', {'folder':self.restore_folder.text(),'target':target})

    def confirm_restore(self):
        if not self.backup_plan or self.sd_busy or not self.sd_ready(): return
        plan = dict(self.backup_plan)
        message = ('Create ' + plan['target'] + ' and restore ' + str(plan['files']) + ' files (' + str(plan['bytes']) + ' bytes)?\n'
                   'No existing files will be overwritten. A cancelled restore may leave this new folder partially populated.')
        if QMessageBox.question(self, 'Confirm previewed restore', message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        self.start_backup_job('restore', '/ext', {'folder':plan['folder'],'target':plan['target'],'manifest_digest':plan['manifest_digest']})

    def backup_operation_finished(self, session, result):
        if session is self.session and not result.get('ok') and self.connection_cancelled:
            self.backup_last_error = result.get('error','Operation cancelled.'); self.backup_status.setText(self.backup_last_error); return
        if session is not self.session or not self.sd_busy or not self.sd_ready(): return
        self.sd_busy = False
        if result.get('ok'):
            self.backup_progress.setValue(100); self.sd_progress.setValue(100)
            self.send_btn.setEnabled(True); self.identify_btn.setEnabled(True)
            self.sd_status.setText('Backup/preview task complete. SD listing remains available.')
            if result['operation'] == 'restore_preview':
                self.backup_plan = {key:result[key] for key in ('folder','target','manifest_digest','files','directories','bytes')}
                lines = ['Destination: ' + result['target'], str(result['files']) + ' files · ' + str(result['directories']) + ' folders · ' + str(result['bytes']) + ' bytes',
                         'Validated payload SHA-256 hashes. Existing destinations are refused.', '']
                lines += ['[D] ' + path for path in result['directory_paths']] + ['[F] ' + path for path in result['paths']]
                self.backup_preview.setPlainText('\n'.join(lines)); self.backup_status.setText('Preview ready. Review the paths, then confirm restore.')
            elif result['operation'] == 'backup':
                self.backup_status.setText('Verified backup complete: ' + result['folder'] + '\n' + str(result['files']) + ' files · ' + str(result['bytes']) + ' bytes')
            else:
                self.backup_status.setText('Restore complete: ' + result['target'] + '\n' + str(result['files']) + ' verified files.')
                self.sd_available = False; self.sd_tree.clear(); self.device_adapter.capabilities -= {'sd_files'}
                self.sd_status.setText('Restore completed. Refresh / Probe SD to browse the restored folder.')
        else:
            self.backup_last_error = result.get('error','Backup or restore failed.')
            self.sd_last_error = self.backup_last_error; self.backup_status.setText(self.backup_last_error)
            self.backup_plan = None; self.send_btn.setEnabled(False); self.identify_btn.setEnabled(False)
            self.sd_available = False; self.sd_tree.clear(); self.device_adapter.capabilities -= {'sd_files'}
        self.update_sd_controls()
