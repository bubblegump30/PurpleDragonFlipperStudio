"""Named local IR libraries and explicitly confirmed one-command device transmission."""
import copy
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QLabel, QPlainTextEdit, QComboBox, QLineEdit, QHBoxLayout,
                              QInputDialog, QMessageBox, QApplication)
from .neon import panel, button
from .ir_files import inspect_ir
from .ir_protocol import signal_command
from .data_io import load_json


class IRWorkspaceMixin:
    def build_ir_workspace(self, lay):
        self.ir_capabilities=None; self.ir_file_warnings=[]; self.ir_last_error=''
        box, layout=panel('IR Workspace')
        hint=QLabel('Organize local signal libraries. Identify in CLI mode, Check IR support, then confirm one selected transmission. No SD card is required.')
        hint.setWordWrap(True); layout.addWidget(hint)
        row=QHBoxLayout(); self.ir_libraries=QComboBox(); self.ir_libraries.setMinimumWidth(140)
        self.ir_libraries.setAccessibleName('Saved IR libraries'); row.addWidget(self.ir_libraries,1)
        for title,handler in [('Save library',self.save_ir_library),('Load',self.load_ir_library),('Rename',self.rename_ir_library),('Remove',self.remove_ir_library)]: row.addWidget(button(title,handler))
        layout.addLayout(row)
        row=QHBoxLayout()
        for title,handler in [('Open .ir',self.open_ir),('Export file',self.export_ir_file),('Export signal',self.export_ir_signal)]: row.addWidget(button(title,handler))
        layout.addLayout(row)
        self.ir_entries=[]; self.ir_filter=QLineEdit(); self.ir_filter.setMaxLength(256); self.ir_filter.setPlaceholderText('Filter signal names…')
        self.ir_signals=QComboBox(); self.ir_signals.setMinimumWidth(150)
        row=QHBoxLayout(); row.addWidget(self.ir_filter,1); row.addWidget(self.ir_signals,1); layout.addLayout(row)
        self.ir_summary=QLabel('No file loaded.'); self.ir_summary.setWordWrap(True); self.ir_summary.setTextFormat(Qt.TextFormat.PlainText); layout.addWidget(self.ir_summary)
        self.ir_preview=QPlainTextEdit(); self.ir_preview.setReadOnly(True); self.ir_preview.setMinimumHeight(220)
        self.ir_preview.setAccessibleName('IR file preview'); layout.addWidget(self.ir_preview)
        self.ir_filter.textChanged.connect(self.filter_ir_signals); self.ir_signals.currentIndexChanged.connect(self.select_ir_signal)
        layout.addWidget(button('Copy file text',lambda:QApplication.clipboard().setText(self.ir_preview.toPlainText())))
        self.ir_probe_btn=button('Check IR support',lambda:self.start_ir_operation('ir_probe'),True); layout.addWidget(self.ir_probe_btn)
        self.ir_transmit_btn=button('Transmit selected signal',self.confirm_ir_transmit,True); layout.addWidget(self.ir_transmit_btn)
        self.ir_cancel_btn=button('Cancel & disconnect',self.sd_cancel); layout.addWidget(self.ir_cancel_btn)
        self.ir_status=QLabel('Device IR support has not been checked.'); self.ir_status.setWordWrap(True); self.ir_status.setTextFormat(Qt.TextFormat.PlainText); layout.addWidget(self.ir_status)
        self.ir_probe_btn.setToolTip('Explicitly queries ir usage/protocols without transmitting.')
        self.ir_transmit_btn.setToolTip('Validate and confirm one ir tx command. Firmware may send its protocol-defined repeat frames.')
        self.ir_cancel_btn.setToolTip('Disconnects the serial session. IR already emitted cannot be recalled.')
        for control in (self.ir_probe_btn,self.ir_transmit_btn,self.ir_cancel_btn): control.setEnabled(False)
        self.refresh_ir_libraries(); lay.addWidget(box)

    def ir_library_data(self, raw=None):
        if raw is None: raw=self.settings.value('ir_libraries','[]')
        if not isinstance(raw,str) or len(raw.encode('utf-8'))>2100000: raise ValueError('Saved IR library store exceeds its limit.')
        data=load_json(raw,2100000)
        if not isinstance(data,list) or len(data)>10: raise ValueError('At most ten IR libraries can be saved.')
        names=set(); total=0
        for item in data:
            if not isinstance(item,dict) or set(item)!={'title','text'}: raise ValueError('Invalid saved IR library.')
            title=item['title']
            if not isinstance(title,str) or not title.strip() or len(title)>80 or any(ord(c)<32 for c in title) or title.casefold() in names: raise ValueError('Invalid or duplicate library name.')
            names.add(title.casefold())
            _,warnings=inspect_ir(item['text'])
            if warnings: raise ValueError('Saved library contains invalid signals; existing data is preserved.')
            total+=len(item['text'].encode('utf-8'))
        if total>2000000: raise ValueError('Saved libraries are limited to 2 MB of IR text.')
        return data

    def store_ir_libraries(self, data):
        raw=json.dumps(data,ensure_ascii=False)
        # Validate the complete candidate before replacing the saved store.
        if len(data)>10 or sum(len(x['text'].encode('utf-8')) for x in data)>2000000 or len(raw.encode('utf-8'))>2100000:
            raise ValueError('Library limit: ten libraries and 2 MB total text.')
        self.ir_library_data(raw)
        self.settings.setValue('ir_libraries',raw); self.refresh_ir_libraries()

    def refresh_ir_libraries(self):
        self.ir_libraries.clear(); self.ir_libraries.addItem('Saved IR libraries',None)
        self.ir_libraries.setToolTip('Saved local IR libraries; loading never transmits.')
        try:
            for item in self.ir_library_data():
                self.ir_libraries.addItem(item['title'],item['title'])
                self.ir_libraries.setItemData(self.ir_libraries.count()-1,item['title'],Qt.ItemDataRole.ToolTipRole)
        except (ValueError,TypeError) as exc:
            self.ir_libraries.setToolTip(str(exc))

    def library_name(self, title='Library name', current=''):
        value,ok=QInputDialog.getText(self,title,'Name (up to 80 characters):',text=current)
        if not ok:return None
        value=value.strip()
        if not value or len(value)>80 or any(ord(c)<32 for c in value): raise ValueError('Enter a readable name up to 80 characters.')
        return value

    def save_ir_library(self):
        try:
            text=self.ir_preview.toPlainText(); _,warnings=inspect_ir(text)
            if warnings: raise ValueError('Resolve all file validation warnings before saving a library.')
            data=self.ir_library_data(); name=self.library_name()
            if name is None:return
            if any(x['title'].casefold()==name.casefold() for x in data): raise ValueError('That name already exists; choose another name.')
            data.append({'title':name,'text':text}); self.store_ir_libraries(data)
        except (ValueError,TypeError) as exc:self.notify('IR libraries',str(exc))

    def load_ir_library(self):
        try:
            title=self.ir_libraries.currentData()
            for item in self.ir_library_data():
                if item['title']==title:self.load_ir_text(item['text'],title);return
        except (ValueError,TypeError) as exc:self.notify('IR libraries',str(exc))

    def rename_ir_library(self):
        try:
            title=self.ir_libraries.currentData()
            if title is None:return
            data=self.ir_library_data(); name=self.library_name('Rename library',title)
            if name is None:return
            if any(x['title']!=title and x['title'].casefold()==name.casefold() for x in data):raise ValueError('That name already exists.')
            for item in data:
                if item['title']==title:item['title']=name
            self.store_ir_libraries(data)
        except (ValueError,TypeError) as exc:self.notify('IR libraries',str(exc))

    def remove_ir_library(self):
        title=self.ir_libraries.currentData()
        if title is None:return
        if QMessageBox.question(self,'Remove saved IR library','Remove this local library? The original .ir file is unchanged.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        try:self.store_ir_libraries([x for x in self.ir_library_data() if x['title']!=title])
        except (ValueError,TypeError) as exc:self.notify('IR libraries',str(exc))

    def load_ir_text(self, text, title):
        entries,warnings=inspect_ir(text)
        self.ir_preview.setPlainText(text); self.ir_entries=entries; self.ir_file_warnings=warnings
        self.filter_ir_signals()
        self.ir_summary.setText(title+' · '+str(len(entries))+' signals · '+str(len(warnings))+' validation warnings.')
        self.ir_summary.setToolTip('\n'.join(warnings[:50]) if warnings else 'IR file fields passed validation. Selected-signal CLI limits and device support are checked separately.')
        self.update_ir_controls()

    def selected_ir_entry(self):
        line=self.ir_signals.currentData()
        return next((x for x in self.ir_entries if x['line']==line),None)

    def export_ir_file(self):
        text=self.ir_preview.toPlainText()
        if text:self.export_text(text,'Export IR file','signals.ir','Flipper infrared (*.ir)')

    def export_ir_signal(self):
        entry=self.selected_ir_entry()
        if not entry:return
        try:
            signal_command(entry, for_cli=False)
            text='Filetype: IR signals file\nVersion: 1\n#\nname: '+entry['name']+'\n'+'\n'.join(k+': '+v for k,v in entry['fields'].items())+'\n'
            self.export_text(text,'Export selected signal','selected-signal.ir','Flipper infrared (*.ir)')
        except ValueError as exc:self.notify('IR export',str(exc))

    def update_ir_controls(self):
        if not hasattr(self,'ir_probe_btn'):return
        ready=self.sd_ready() and not getattr(self,'sd_busy',False)
        self.ir_probe_btn.setEnabled(bool(ready)); self.ir_cancel_btn.setEnabled(bool(getattr(self,'sd_busy',False)))
        self.ir_transmit_btn.setToolTip('Requires a valid file, identified CLI session and current IR support check.')
        supported=False; entry=self.selected_ir_entry()
        if ready and self.ir_capabilities and entry and not self.ir_file_warnings:
            try:
                signal_command(entry)
                supported=(entry['fields']['type']=='raw' and self.ir_capabilities['raw']) or entry['fields'].get('protocol') in self.ir_capabilities['protocols']
                self.ir_transmit_btn.setToolTip('Confirms one IR command; appliance response is not verified.' if supported else 'Device did not advertise this signal format.')
            except ValueError as exc:self.ir_transmit_btn.setToolTip(str(exc))
        self.ir_transmit_btn.setEnabled(bool(supported))

    def reset_ir_session(self):
        if not hasattr(self,'ir_probe_btn'):return
        self.ir_capabilities=None
        self.device_adapter.capabilities-={'ir_tx'}
        self.ir_status.setText(self.ir_last_error or 'Device IR support has not been checked. Identify and probe again after reconnecting.')
        self.update_ir_controls()

    def start_ir_operation(self, operation, request=None):
        if not self.sd_ready() or self.sd_busy:return
        if operation=='ir_transmit' and not self.ir_capabilities:return
        if not self.session.request_storage(operation,'/ext',request):
            self.ir_status.setText('Serial queue is busy. Wait for pending commands.');return
        self.sd_busy=True; self.ir_last_error=''; self.send_btn.setEnabled(False); self.identify_btn.setEnabled(False)
        if operation=='ir_probe':
            self.ir_capabilities=None; self.device_adapter.capabilities-= {'ir_tx'}
        self.ir_status.setText('Checking device IR support…' if operation=='ir_probe' else 'Executing one IR transmit command… Target response cannot be verified here.')
        self.update_sd_controls()

    def confirm_ir_transmit(self):
        if not self.ir_transmit_btn.isEnabled():return
        entry=copy.deepcopy(self.selected_ir_entry()); command=signal_command(entry)
        box=QMessageBox(self); box.setWindowTitle('Confirm IR transmission'); box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText('Transmit "'+entry['name']+'" using one command?\n'+command+'\nAim at the intended device. The appliance response is not verified by this app.')
        box.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No); box.setDefaultButton(QMessageBox.StandardButton.No)
        if box.exec()!=QMessageBox.StandardButton.Yes:return
        self.start_ir_operation('ir_transmit',{'entry':entry,'capabilities':copy.deepcopy(self.ir_capabilities)})

    def ir_operation_finished(self, session, result):
        if session is self.session and not result.get('ok') and self.connection_cancelled:
            self.ir_last_error=result.get('error','IR command cancelled.'); self.ir_status.setText(self.ir_last_error);return
        if session is not self.session or not self.sd_busy or not self.sd_ready():return
        self.sd_busy=False
        if result.get('ok'):
            if result['operation']=='ir_probe':
                self.ir_capabilities={'protocols':result['protocols'],'raw':result['raw']}
                self.device_adapter.capabilities|={'ir_tx'}
                self.ir_status.setText('IR CLI support checked: '+', '.join(result['protocols'])+(' · RAW' if result['raw'] else ''))
            else:self.ir_status.setText('IR CLI command completed. Appliance reception/action has not been verified.')
            self.send_btn.setEnabled(True); self.identify_btn.setEnabled(True)
        else:
            self.ir_last_error=result.get('error','IR command failed.'); self.ir_status.setText(self.ir_last_error)
            self.ir_capabilities=None; self.device_adapter.capabilities-={'ir_tx'}
            self.send_btn.setEnabled(False); self.identify_btn.setEnabled(False)
        self.update_sd_controls()
