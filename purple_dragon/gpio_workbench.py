"""Connection-scoped digital controls integrated into the existing GPIO Lab."""
from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QMessageBox, QHBoxLayout
from .neon import button
from .gpio_protocol import PINS


class GPIOWorkbenchMixin:
    def init_gpio_workbench(self, layout):
        self.gpio_supported=False; self.gpio_states={}; self.gpio_pending=None
        self.gpio_timer=QTimer(self); self.gpio_timer.setInterval(1000); self.gpio_timer.timeout.connect(self.gpio_poll_tick)
        self.gpio_probe_btn=button('Check GPIO support',lambda:self.start_gpio_operation('gpio_probe'))
        self.gpio_cancel_btn=button('Cancel & disconnect',self.sd_cancel)
        row=QHBoxLayout();row.addWidget(self.gpio_probe_btn);row.addWidget(self.gpio_cancel_btn);layout.addLayout(row)
        self.gpio_status.setText('Identify in CLI mode, then Check GPIO support. No SD card required. Disconnect does not reset physical outputs.')
        self.arm.setToolTip('Arm the GPIO backend only after Output succeeds; changing pins or reconnecting disarms.')
        self.poll.setToolTip('Read-only GPIO backend polling at most once per second. Stops on pin change, errors or leaving GPIO Lab.')
        self.pin.currentTextChanged.connect(self.gpio_pin_changed)
        self.arm.toggled.connect(lambda *_:self.update_gpio_controls())
        self.poll.toggled.connect(self.gpio_poll_changed)
        self.history.document().setMaximumBlockCount(500)
        self.gpio_response.document().setMaximumBlockCount(100)
        self.update_gpio_controls()

    def gpio_pin(self):return self.pin.currentText().split(' ',1)[0]

    def gpio_pin_changed(self, *_):
        self.arm.setChecked(False);self.poll.setChecked(False);self.update_gpio_controls()

    def gpio_poll_changed(self, checked):
        if checked and self.gpio_can_read():self.gpio_timer.start()
        else:self.gpio_timer.stop()

    def gpio_can_read(self):
        return bool(self.sd_ready() and self.gpio_supported and self.gpio_states.get(self.gpio_pin(),{}).get('mode')=='Input')

    def gpio_poll_tick(self):
        if self.workspace.currentText()!='GPIO Lab' or not self.gpio_can_read():
            self.poll.setChecked(False);return
        if not self.sd_busy:self.start_gpio_operation('gpio_action',{'pin':self.gpio_pin(),'action':'Read'})

    def update_gpio_controls(self):
        if not hasattr(self,'gpio_probe_btn'):return
        ready=self.sd_ready() and not getattr(self,'sd_busy',False)
        state=self.gpio_states.get(self.gpio_pin(),{}); mode=state.get('mode')
        enabled=ready and self.gpio_supported
        self.gpio_probe_btn.setEnabled(bool(ready));self.gpio_cancel_btn.setEnabled(bool(getattr(self,'sd_busy',False)))
        self.pin.setEnabled(not getattr(self,'sd_busy',False))
        for action,control in self.gpio_buttons.items():
            allowed=enabled and (action in ('Input','Output') or (action=='Read' and mode=='Input') or (action in ('LOW','HIGH') and mode=='Output' and self.arm.isChecked()))
            control.setEnabled(bool(allowed));control.setToolTip('Check GPIO support; set Input before reading, Output and arm before writing. Output starts LOW.')
        self.arm.setEnabled(bool(enabled and mode=='Output'))
        self.poll.setEnabled(bool(enabled and mode=='Input'))
        self.gpio_mode_value.setText(mode or 'Unknown')
        value=state.get('value');self.gpio_state_value.setText('Unknown' if value is None else ('HIGH (1)' if value else 'LOW (0)'))
        self.gpio_direction_value.setText(mode or 'Unknown')

    def reset_gpio_session(self):
        if not hasattr(self,'gpio_probe_btn'):return
        self.gpio_supported=False;self.gpio_states={};self.gpio_pending=None
        self.arm.setChecked(False);self.poll.setChecked(False);self.gpio_timer.stop()
        self.device_adapter.capabilities-={'gpio_digital'}
        self.gpio_status.setText('GPIO state unknown. Identify and check support again. Physical outputs may remain active; disconnect does not reset pins.')
        self.update_gpio_controls()

    def start_gpio_operation(self, operation, request=None):
        if not self.sd_ready() or self.sd_busy:return
        if operation=='gpio_action' and not self.gpio_supported:return
        if not self.session.request_storage(operation,'/ext',request):
            self.gpio_status.setText('Serial queue busy; wait before retrying.');return
        if operation=='gpio_probe':self.reset_gpio_session()
        self.gpio_pending=(operation,dict(request or {}));self.sd_busy=True
        self.send_btn.setEnabled(False);self.identify_btn.setEnabled(False)
        self.gpio_status.setText('Checking GPIO command support…' if operation=='gpio_probe' else 'Waiting for GPIO response…')
        self.update_sd_controls()

    def gpio_action(self, action):
        if action not in self.gpio_buttons or not self.gpio_buttons[action].isEnabled():return
        if action!='Read':self.poll.setChecked(False)
        pin=self.gpio_pin()
        if action=='Output':
            answer=QMessageBox.question(self,'Confirm GPIO output',pin+' (header '+str(PINS[pin])+') will become a push-pull OUTPUT starting LOW.\nDisconnect attached boards/drivers before changing wiring. Use 3.3 V compatible circuitry and common ground. Do not connect competing outputs.\nEnable output now?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes:return
            self.arm.setChecked(False)
        self.start_gpio_operation('gpio_action',{'pin':pin,'action':action})

    def gpio_operation_finished(self, session, result):
        if session is not self.session or not self.sd_busy or self.gpio_pending is None or not self.sd_ready():return
        operation,request=self.gpio_pending
        if result.get('operation')!=operation:return
        self.gpio_pending=None;self.sd_busy=False
        if not result.get('ok'):
            self.reset_gpio_session();self.gpio_status.setText(result.get('error','GPIO operation failed.')+' Physical state is unknown; reconnect before retrying.')
            self.send_btn.setEnabled(False);self.identify_btn.setEnabled(False);self.update_sd_controls();return
        if operation=='gpio_probe':
            self.gpio_supported=True;self.device_adapter.capabilities|={'gpio_digital'}
            self.gpio_status.setText('Digital GPIO CLI checked. Select Input before Read; Output starts LOW. State reflects the last confirmed command, not continuous hardware monitoring.')
        else:
            pin=request['pin'];action=request['action']
            if result.get('pin')!=pin or result.get('action')!=action:
                self.reset_gpio_session();self.update_sd_controls();return
            state=self.gpio_states.setdefault(pin,{'mode':'Unknown','value':None})
            if action in ('Input','Output'):state['mode']=action
            state['value']=result['value']
            text=datetime.now().astimezone().isoformat(timespec='seconds')+' · '+result['response']
            scroll=self.history.verticalScrollBar().value()
            self.gpio_response.appendPlainText(text);self.history.appendPlainText(text)
            if self.autoscroll.isChecked():self.history.verticalScrollBar().setValue(self.history.verticalScrollBar().maximum())
            else:self.history.verticalScrollBar().setValue(scroll)
            self.gpio_status.setText(result['response']+' · Last confirmed CLI response; no voltage measurement.')
        self.send_btn.setEnabled(True);self.identify_btn.setEnabled(True);self.update_sd_controls()
