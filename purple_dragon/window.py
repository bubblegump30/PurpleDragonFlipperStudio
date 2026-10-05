"""Dense neon console layout derived from the user's supplied visual reference."""
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,QMainWindow,QWidget,QFrame,QLabel,QVBoxLayout,QHBoxLayout,QGridLayout,
    QComboBox,QPlainTextEdit,QCheckBox,QStackedWidget,QScrollArea,QButtonGroup,
    QPushButton,QLineEdit,
    QBoxLayout, QSplitter,
)
from . import base_window as base
from .base_window import ASSETS, WEBSITE, label
from .backend import HardwareAdapter
from .theme import THEMES, stylesheet
from .neon import NeonButton,NeonPanel,HeaderArt,ChipArt,panel,button,icon
from .matrix import MatrixRain
from . import __version__

class MainWindow(base.WorkspaceServices):
    def __init__(self,adapter=None,settings=None):
        QMainWindow.__init__(self)
        self.settings=settings or QSettings('PurpleDragonFoundation','FlipperGUI')
        self.adapter=adapter or HardwareAdapter()
        self.session=None;self.connected=False;self.port_info={}
        self.last_connection_error=None;self.connection_cancelled=False
        self.connection_state="disconnected";self.connection_lost=False;self.last_session_port=None
        self.navigation_history=[];self.navigation_cursor=-1;self.shortcut_actions={}
        self.setWindowTitle('Purple Dragon | Flipper GPIO & UART Lab • GUI '+__version__)
        self.setWindowIcon(QIcon(str(ASSETS/'dragon.ico')))
        self.resize(1672,941);self.setMinimumSize(980,760)
        if self.settings.value('design_revision',0,type=int)<2:
            self.settings.setValue('intensity',85)
            self.settings.setValue('speed',70)
            self.settings.setValue('design_revision',2)
        self.shell=QWidget();self.setCentralWidget(self.shell)
        self.rain=MatrixRain(self.shell)
        outer=QHBoxLayout(self.shell);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        self.build_sidebar(outer)
        self.content=QWidget();self.content.setObjectName('content');outer.addWidget(self.content,1)
        body=QVBoxLayout(self.content);body.setContentsMargins(4,0,7,4);body.setSpacing(3)
        self.art_header=HeaderArt();body.addWidget(self.art_header)
        body.addWidget(self.build_connection())
        body.addWidget(self.build_workspace_strip())
        self.tab_container=NeonPanel();self.tab_grid=QGridLayout(self.tab_container)
        self.tab_grid.setContentsMargins(0,0,0,0);self.tab_grid.setSpacing(0)
        self.tab_buttons={};self.tabs_group=QButtonGroup(self)
        self.tabs_group.setExclusive(True)
        for name,title,glyph in [
            ('GPIO Lab','GPIO LAB','cpu'),('UART Console','UART CONSOLE','terminal'),
            ('Flipper App','FLIPPER APP','cube'),('Device Dashboard','DEVICE DASHBOARD','gauge'),
            ('IR Remote Studio','IR REMOTE STUDIO','radio'),('Backup & Tools','BACKUP & TOOLS','folder'),
            ('Live Log','LIVE LOG','list'),('Apps & NFC','APPS & NFC','radio'),
        ]:
            btn=NeonButton(title,lambda checked=False,n=name:self.navigate(n),'nav',glyph)
            btn.setCheckable(True);btn.setMinimumHeight(51);btn.compact=True
            self.tabs_group.addButton(btn);self.tab_buttons[name]=btn
        body.addWidget(self.tab_container)
        self.stack=QStackedWidget();body.addWidget(self.stack,1)
        self.pages={}
        for name,builder in [
            ('GPIO Lab',self.build_gpio),('UART Console',self.build_console),
            ('Flipper App',self.build_flipper_app),('Device Dashboard',self.build_device),
            ('IR Remote Studio',self.build_ir),('Backup & Tools',self.build_tools),
            ('Apps & NFC',self.build_apps),('Live Log',self.build_log),('Appearance',self.build_appearance),
        ]:
            page=QWidget();page.setObjectName('content');page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
            lay=QVBoxLayout(page);lay.setContentsMargins(0,0,0,0);lay.setSpacing(6)
            builder(lay)
            if name!='GPIO Lab':lay.addStretch()
            scroll=QScrollArea();scroll.setWidgetResizable(True)
            scroll.viewport().setAutoFillBackground(False);scroll.setWidget(page);page.setAutoFillBackground(False)
            self.pages[name]=self.stack.addWidget(scroll)
        self.pages['Command Center']=self.pages['GPIO Lab']
        self.metrics={name:QLabel(self) for name in ['CONNECTION','WORKSPACE','DEVICE TELEMETRY']}
        for metric in self.metrics.values():metric.hide()
        self.activity=label('','muted');self.activity.setMaximumHeight(22)
        self.activity.setTextFormat(Qt.TextFormat.PlainText);body.addWidget(self.activity)
        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().showMessage('Neon GUI v'+__version__+' · Created by KyleAustinHillier @PurpleDragonFoundationLtd')
        self.inline_theme.currentTextChanged.connect(self.change_inline_theme)
        self.workspace.currentTextChanged.connect(self.workspace_changed)
        self.port.currentIndexChanged.connect(self.port_selected)
        self.mode.currentTextChanged.connect(self.save_port_preferences)
        self.baud.currentTextChanged.connect(self.save_port_preferences)
        self.apply_theme();self.reflow();self.refresh_ports()
        self.connection_timer=QTimer(self)
        self.connection_timer.setInterval(1500)
        self.connection_timer.timeout.connect(self.monitor_connection)
        self.connection_timer.start()
        self.install_shortcuts()
        last=self.settings.value('last_workspace','Command Center')
        self.navigate(last if isinstance(last,str) and last in self.pages else 'Command Center')
        self.geometry_restored=False
        geometry=self.settings.value('window_geometry')
        if geometry:
            self.geometry_restored=self.restoreGeometry(geometry)
            if not any(screen.availableGeometry().intersects(self.frameGeometry()) for screen in QApplication.screens()):
                self.move(QApplication.primaryScreen().availableGeometry().topLeft())
        self.log('Ready • Device services await RC7 integration; serial and local tools are available.')

    def build_sidebar(self,outer):
        sidebar=QFrame();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(172)
        outer.addWidget(sidebar)
        lay=QVBoxLayout(sidebar);lay.setContentsMargins(3,14,3,12);lay.setSpacing(5)
        self.nav={};self.nav_group=QButtonGroup(self);self.nav_group.setExclusive(True)
        for name,text,glyph in [
            ('Command Center','Home','home'),('GPIO Lab','GPIO & UART','cpu'),
            ('UART Console','UART Console','terminal'),('Flipper App','Flipper App','cube'),
            ('Device Dashboard','Device\nDashboard','gauge'),('IR Remote Studio','IR Remote\nStudio','radio'),
            ('Backup & Tools','Backup & Tools','folder'),('Live Log','Live Log','list'),('Apps & NFC','Apps & NFC','radio'),
        ]:
            btn=NeonButton(text,lambda checked=False,n=name:self.navigate(n),'nav',glyph)
            btn.setCheckable(True);btn.setMinimumHeight(54)
            self.nav_group.addButton(btn);self.nav[name]=btn;lay.addWidget(btn)
        lay.addStretch(1)
        separator=QFrame();separator.setObjectName('separator');separator.setFixedHeight(1);lay.addWidget(separator)
        lay.addWidget(NeonButton('Settings',lambda:self.navigate('Appearance'),'nav','settings'))
        theme=NeonButton('Themes',lambda:self.navigate('Appearance'),'nav','palette')
        theme.setCheckable(True);self.nav['Appearance']=theme;self.nav_group.addButton(theme);lay.addWidget(theme)
        lay.addWidget(NeonButton('About',self.about,'nav','info'))

    def build_connection(self):
        container=NeonPanel();container.setObjectName('connectionPanel')
        self.connection_grid=QGridLayout(container);self.connection_grid.setContentsMargins(13,10,13,10);self.connection_grid.setSpacing(9)
        self.port=QComboBox();self.port.setMinimumWidth(110);self.port.setMaximumWidth(185)
        self.port.setToolTip('Select a detected USB serial port.')
        self.refresh_btn=NeonButton('Refresh',self.refresh_ports,'blue','refresh');self.refresh_btn.setFixedWidth(108)
        self.mode=QComboBox();self.mode.addItems(['CLI','UART Bridge']);self.mode.setCurrentText(self.settings.value('mode','CLI'))
        self.mode.setMinimumWidth(86);self.mode.setMaximumWidth(120)
        self.mode.setToolTip('Bridge configuration requires the device backend or configuration on the device.')
        self.baud=QComboBox();self.baud.addItems(['9600','19200','38400','57600','115200','230400','460800','921600'])
        self.baud.setCurrentText(str(self.settings.value('baud','230400')));self.baud.setMinimumWidth(100);self.baud.setMaximumWidth(130)
        self.connect_btn=NeonButton('Connect',self.toggle_connection,'primary','plug');self.connect_btn.setFixedWidth(136)
        self.refresh_btn.setToolTip('Refresh the list of available USB serial ports.')
        self.connect_btn.setToolTip('Open the selected serial port; this does not verify device identity.')
        self.baud.setToolTip('Choose the baud rate expected by the selected device or UART bridge.')
        self.badge=label('○  Disconnected','connectionStatus');self.badge.setMinimumWidth(118)
        self.connection_message=label('Select a port and connect.','muted')
        self.connection_message.setTextFormat(Qt.TextFormat.PlainText)
        self.connection_message.setMaximumHeight(26)
        self.connection_message.setMaximumWidth(194)
        self.inline_theme=QComboBox();self.inline_theme.addItems(THEMES);self.inline_theme.setCurrentText(self.settings.value('theme','Neo Purple'))
        for i,(name,color) in enumerate(THEMES.items()):
            pix=QPixmap(18,18);pix.fill(Qt.GlobalColor.transparent)
            paint=QPainter(pix);paint.setRenderHint(QPainter.RenderHint.Antialiasing);paint.setBrush(QColor(color));paint.setPen(Qt.PenStyle.NoPen);paint.drawEllipse(2,2,14,14);paint.end()
            self.inline_theme.setItemIcon(i,QIcon(pix))
        self.inline_theme.setToolTip("Change the accent palette; your choice is saved automatically.")
        self.inline_theme.setMinimumWidth(135);self.inline_theme.setMaximumWidth(185)
        self.connection_sections=[]
        for entries in [
            [('PORT',self.port),('',self.refresh_btn)],
            [('MODE',self.mode),('BAUD',self.baud)],
            [('',self.connect_btn),('',self.badge)],
            [('Theme',self.inline_theme)],
        ]:
            section=QWidget();row=QHBoxLayout(section);row.setContentsMargins(0,0,0,0);row.setSpacing(8)
            for title,widget in entries:
                if title:row.addWidget(label(title))
                if widget is self.badge:
                    status=QVBoxLayout();status.setSpacing(1);status.addWidget(self.badge);status.addWidget(self.connection_message);row.addLayout(status)
                else:row.addWidget(widget)
            self.connection_sections.append(section)
        return container

    def build_workspace_strip(self):
        item=NeonPanel();row=QHBoxLayout(item);row.setContentsMargins(15,1,5,1);row.setSpacing(10)
        row.addWidget(label('Workspace'))
        self.workspace=QComboBox();self.workspace.setMinimumWidth(155)
        self.workspace.addItems(['GPIO Lab','UART Console','Flipper App','Device Dashboard','IR Remote Studio','Backup & Tools','Live Log','Apps & NFC','Appearance'])
        row.addWidget(self.workspace)
        hint=label('ⓘ  New to Flipper? Start with CLI mode. UART Bridge talks to a separate wired device.','muted')
        row.addWidget(hint,1)
        self.foundation_button=NeonButton('Purple Dragon Foundation',lambda:self.open_url(WEBSITE),'purple','globe')
        self.foundation_button.setFixedWidth(257);row.addWidget(self.foundation_button)
        return item

    def build_gpio(self,lay):
        workspace=NeonPanel(tone='accent');w=QVBoxLayout(workspace)
        w.setContentsMargins(12,8,12,12);w.setSpacing(4)
        banner=QWidget();banner.setFixedHeight(70);banner_row=QHBoxLayout(banner);banner_row.setContentsMargins(15,0,8,0)
        cpu=QLabel();cpu.setPixmap(icon('cpu','#edd7ff').pixmap(43,43));banner_row.addWidget(cpu)
        copy=QVBoxLayout();copy.setSpacing(3)
        self.heading=label('GPIO Lab','title');copy.addWidget(self.heading)
        copy.addWidget(label('Control and monitor GPIO pins on your Flipper Zero. GPIO and UART Bridge use separate modes.','muted'))
        banner_row.addLayout(copy,1)
        art=ChipArt();art.setMinimumSize(130,60);art.setMaximumWidth(345);banner_row.addWidget(art,1)
        w.addWidget(banner)
        upper=QHBoxLayout();upper.setSpacing(3)
        self.gpio_upper=upper
        self.gpio_top_splitter=QSplitter(Qt.Orientation.Horizontal)
        self.gpio_top_splitter.setChildrenCollapsible(False)
        self.gpio_top_splitter.setHandleWidth(9)
        self.gpio_top_splitter.setToolTip('Drag the divider to resize Pin Control and Setup & Presets. Ctrl+Shift+0 resets panel sizes.')
        self.gpio_top_splitter.splitterMoved.connect(lambda *_: self.save_workspace_panels())
        upper.addWidget(self.gpio_top_splitter)
        pins,p=panel();p.setSpacing(7)
        p.addWidget(label('♟  Pin Control','sectionTitle'))
        controls=QGridLayout();controls.setSpacing(5)
        self.gpio_controls=controls
        self.pin=QComboBox();self.pin.setMinimumWidth(130)
        self.pin.addItems(['PA7 (pin 2)','PA6 (pin 3)','PA4 (pin 4)','PB3 (pin 5)','PB2 (pin 6)','PC3 (pin 7)','PC1 (pin 15)','PC0 (pin 16)'])
        controls.addWidget(self.pin,0,0)
        self.gpio_buttons={}
        for action,role,glyph in [('Input','purple','input'),('Output','cyan','output'),('Read','blue','search'),('LOW','neutral','down'),('HIGH','red','up')]:
            btn=NeonButton(action,lambda checked=False,a=action:self.gpio_action(a),role,glyph)
            btn.setEnabled(False);btn.setToolTip('Requires the RC7 GPIO backend and a device connection.')
            self.gpio_buttons[action]=btn;controls.addWidget(btn,0,len(self.gpio_buttons))
        p.addLayout(controls)
        toggles=QHBoxLayout()
        self.gpio_toggles=toggles
        self.arm=QCheckBox('Arm LOW/HIGH after Output succeeds');self.arm.setEnabled(False)
        self.poll=QCheckBox('Read selected pin every second');self.poll.setEnabled(False)
        toggles.addWidget(self.arm);toggles.addWidget(self.poll);toggles.addStretch();p.addLayout(toggles)
        p.addWidget(label("GPIO controls unavailable · Connect the RC7 backend to enable hardware actions.","muted"))
        self.arm.setToolTip("Arming is available only after the GPIO backend confirms Output mode.")
        self.poll.setToolTip("Polling requires the GPIO backend and a verified device session.")
        self.gpio_top_splitter.addWidget(pins)
        presets,p=panel();p.setSpacing(7);p.addWidget(label('⚙  Setup & Presets','sectionTitle'))
        row=QHBoxLayout();row.setSpacing(5)
        self.profile=QComboBox();self.profile.setEditable(True);self.profile.setMinimumWidth(100)
        self.profile_name=self.profile.lineEdit();self.profile_name.setPlaceholderText('Setup name…')
        row.addWidget(self.profile,2)
        row.addWidget(NeonButton('Save Setup',self.save_profile,'purple','save'),1)
        row.addWidget(NeonButton('Delete',self.delete_profile,'neutral','trash'),1);p.addLayout(row)
        note=QHBoxLayout();note.addWidget(label('▤  Note'))
        self.notes=QPlainTextEdit();self.notes.setPlaceholderText('Add a note about this setup…');self.notes.setFixedHeight(42)
        note.addWidget(self.notes,1);p.addLayout(note)
        actions=QHBoxLayout();actions.setSpacing(5)
        for title,handler in [('New',self.new_profile),('Duplicate',self.duplicate_profile),('Rename',self.rename_profile)]:
            btn=NeonButton(title,handler,'neutral');btn.setMinimumHeight(34);actions.addWidget(btn)
        p.addLayout(actions)
        self.profile_feedback=label('Local setups · Rename uses the name entered above.','muted');p.addWidget(self.profile_feedback)
        self.gpio_top_splitter.addWidget(presets)
        w.addLayout(upper)
        middle=QHBoxLayout();middle.setSpacing(3)
        self.gpio_middle=middle
        self.gpio_info_splitter=QSplitter(Qt.Orientation.Horizontal)
        self.gpio_info_splitter.setChildrenCollapsible(False)
        self.gpio_info_splitter.setHandleWidth(9)
        self.gpio_info_splitter.setToolTip('Drag the divider to resize Latest GPIO Response and Pin Information.')
        self.gpio_info_splitter.splitterMoved.connect(lambda *_: self.save_workspace_panels())
        middle.addWidget(self.gpio_info_splitter)
        response,r=panel();r.setSpacing(4)
        response_header=QHBoxLayout();response_header.addWidget(label('⌁  Latest GPIO Response','sectionTitle'),1)
        clear=NeonButton('Clear',lambda:self.gpio_response.clear(),'neutral','trash');clear.setFixedSize(91,36);response_header.addWidget(clear)
        r.addLayout(response_header)
        self.gpio_response=QPlainTextEdit();self.gpio_response.setObjectName('gpioResponse');self.gpio_response.setReadOnly(True)
        self.gpio_response.setMinimumHeight(97);self.gpio_response.setMaximumHeight(130)
        self.gpio_response.setPlainText('Choose a pin and connect to view its response.\n[INFO] Use Input before Read; use Output and arm before LOW/HIGH.\n[INFO] Only connect 3.3 V compatible circuitry. Device backend required.')
        r.addWidget(self.gpio_response);self.gpio_info_splitter.addWidget(response)
        info,inf=panel();inf.setSpacing(4);inf.addWidget(label('ⓘ  Pin Information','sectionTitle'))
        info_body=QHBoxLayout();grid=QGridLayout();grid.setVerticalSpacing(3)
        self.pin_value=label(self.pin.currentText());self.pin_value.setObjectName('pinValue')
        for i,(title,value) in enumerate([('Selected Pin',self.pin_value),('Mode',label('—')),('Last State',label('—')),('Voltage (3.3 V)',label('—')),('Direction',label('—'))]):
            grid.addWidget(label(title,'muted'),i,0);grid.addWidget(value,i,1)
        info_body.addLayout(grid,3);chip=ChipArt(kind='blue');chip.setMinimumSize(115,100);info_body.addWidget(chip,2)
        inf.addLayout(info_body);self.gpio_info_splitter.addWidget(info);w.addLayout(middle)
        history,h=panel();h.setSpacing(3)
        tools=QHBoxLayout();tools.addWidget(label('☷  Input History','sectionTitle'),1)
        export_btn=NeonButton('Export',self.export_history,'neutral','list');export_btn.setFixedSize(104,36);tools.addWidget(export_btn)
        clear_btn=NeonButton('Clear',lambda:self.history.clear(),'neutral','trash');clear_btn.setFixedSize(95,36);tools.addWidget(clear_btn)
        self.autoscroll=QCheckBox('Auto Scroll');self.autoscroll.setChecked(True);tools.addWidget(self.autoscroll)
        h.addLayout(tools)
        self.history=QPlainTextEdit();self.history.setReadOnly(True);self.history.setPlaceholderText('>  Waiting for GPIO readings…')
        self.history.setFixedHeight(48);h.addWidget(self.history);w.addWidget(history)
        lay.addWidget(workspace)
        self.profile.currentIndexChanged.connect(self.load_profile)
        self.pin.currentTextChanged.connect(self.pin_value.setText)
        self.refresh_profiles()

    def build_flipper_app(self,lay):
        box,b=panel('Flipper App')
        b.addWidget(label('Official apps, local files, and your device workspace.','muted'))
        b.addWidget(NeonButton('Open official app catalog',lambda:self.open_url('https://lab.flipper.net/apps'),'purple','cube'))
        b.addWidget(NeonButton('Open NFC apps',lambda:self.open_url('https://lab.flipper.net/apps/category/nfc'),'blue','radio'))
        b.addWidget(label('Device app installation requires the existing RC7 app service.','muted'));lay.addWidget(box)

    def gpio_action(self,action):
        self.gpio_response.appendPlainText('[INFO] '+action+' needs the connected RC7 GPIO service.')

    def export_history(self):
        self.export_text(self.history.toPlainText(),'Export GPIO history','gpio-history.txt','Text files (*.txt)')

    def about(self):
        self.notify('Purple Dragon','Purple Dragon GPIO & UART Lab\nNeon GUI v'+__version__+'\nCreated by KyleAustinHillier @PurpleDragonFoundationLtd\n\nRebuilt around your supplied neon-console design.\n'+WEBSITE)

    def workspace_changed(self,name):
        self.navigate(name)

    def refresh_ports(self):
        super().refresh_ports()
        self.connection_message.setToolTip(self.connection_message.text())

    def navigate(self,name,record=True):
        if not hasattr(self,'pages') or name not in self.pages:return
        self.stack.setCurrentIndex(self.pages[name]);actual='GPIO Lab' if name=='Command Center' else name
        self.heading.setText(actual)
        self.nav[name].setChecked(True)
        self.workspace.blockSignals(True);self.workspace.setCurrentText(actual);self.workspace.blockSignals(False)
        self.tabs_group.setExclusive(False)
        for page,btn in self.tab_buttons.items():btn.setChecked(page==actual)
        self.tabs_group.setExclusive(True)
        self.settings.setValue('last_workspace',name)
        if record:
            current=self.navigation_history[self.navigation_cursor] if self.navigation_cursor>=0 else None
            current_actual='GPIO Lab' if current=='Command Center' else current
            if current_actual==actual:
                self.navigation_history[self.navigation_cursor]=name
            else:
                self.navigation_history=self.navigation_history[:self.navigation_cursor+1]+[name]
                self.navigation_history=self.navigation_history[-64:]
                self.navigation_cursor=len(self.navigation_history)-1
        self.update_navigation_actions()

    def install_shortcuts(self):
        shortcuts=[('Back','Alt+Left',lambda:self.travel(-1)),('Forward','Alt+Right',lambda:self.travel(1)),
            ('Home','Ctrl+Home',lambda:self.navigate('Command Center')),
            ('Appearance','Ctrl+,',lambda:self.navigate('Appearance')),
            ('Console input','Ctrl+L',self.focus_console),('Refresh ports','F5',self.refresh_ports),
            ('Beginner guide','F1',self.beginner_guide),
            ('Workspace selector','Ctrl+K',self.focus_workspace_selector),
            ('Transcript search','Ctrl+F',self.focus_transcript_search),
            ('Reset panel sizes','Ctrl+Shift+0',self.reset_workspace_panels)]
        for i,name in enumerate(self.tab_buttons,1):
            shortcuts.append((name,'Ctrl+'+str(i),lambda checked=False,n=name:self.navigate(n)))
        for title,key,callback in shortcuts:
            action=QAction(title,self);action.setShortcut(QKeySequence(key))
            action.triggered.connect(callback);self.addAction(action);self.shortcut_actions[title]=action
        for i,(name,btn) in enumerate(self.tab_buttons.items(),1):
            tip=name+' · Ctrl+'+str(i)
            btn.setToolTip(tip);self.nav[name].setToolTip(tip)
        self.workspace.setToolTip('Select a workspace · Ctrl+K. Alt+Left / Alt+Right navigate your session history.')
        self.workspace.setAccessibleName('Workspace selector')
        self.console_search.setToolTip('Search retained displayed text · Ctrl+F opens Console search. Enter finds the next match.')
        self.console_search.setAccessibleName('Transcript search')
        self.command.setAccessibleName('Serial command draft')
        self.port.setAccessibleName('Serial port')
        self.pin.setToolTip('Select a GPIO pin for local setup notes. Hardware actions require the backend.')
        self.notes.setToolTip('Local setup notes. Save Setup stores the selected pin and notes.')
        self.baud.setToolTip('Serial baud rate. Saved per port; change while disconnected.')
        self.ending.setToolTip('Line ending appended only when you explicitly Send a command.')
        self.console_pause.setToolTip('Freeze the display while continuing bounded capture; uncheck to catch up.')
        self.command_favorites.setAccessibleName('Saved command favorites')
        self.update_navigation_actions()

    def update_navigation_actions(self):
        if 'Back' in self.shortcut_actions:
            self.shortcut_actions['Back'].setEnabled(self.navigation_cursor>0)
            self.shortcut_actions['Forward'].setEnabled(self.navigation_cursor<len(self.navigation_history)-1)

    def travel(self,offset):
        target=self.navigation_cursor+offset
        if 0<=target<len(self.navigation_history):
            self.navigation_cursor=target
            self.navigate(self.navigation_history[target],record=False)

    def focus_console(self):
        self.navigate('UART Console');self.command.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.stack.currentWidget().ensureWidgetVisible(self.command)

    def focus_workspace_selector(self):
        self.workspace.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.workspace.showPopup()

    def focus_transcript_search(self):
        self.navigate('UART Console')
        self.console_search.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.console_search.selectAll()
        self.stack.currentWidget().ensureWidgetVisible(self.console_search)

    def save_workspace_panels(self):
        mode = getattr(self, 'panel_layout_mode', None)
        if mode:
            for name, splitter in [('top', self.gpio_top_splitter), ('info', self.gpio_info_splitter)]:
                self.settings.setValue('panels/' + mode + '/' + name, splitter.sizes())

    def restore_workspace_panels(self, compact):
        mode = 'compact' if compact else 'wide'
        if getattr(self, 'panel_layout_mode', None) == mode:
            return
        self.panel_layout_mode = mode
        orientation = Qt.Orientation.Vertical if compact else Qt.Orientation.Horizontal
        for name, splitter in [('top', self.gpio_top_splitter), ('info', self.gpio_info_splitter)]:
            splitter.setOrientation(orientation)
            sizes = self.settings.value('panels/' + mode + '/' + name, [600, 400])
            try:
                sizes = [int(x) for x in sizes]
                if len(sizes) != 2 or any(x <= 0 or x > 100000 for x in sizes):
                    raise ValueError('Invalid splitter sizes')
            except (ValueError, TypeError):
                sizes = [600, 400]
            splitter.setSizes(sizes)

    def reset_workspace_panels(self):
        for mode in ('compact', 'wide'):
            for name in ('top', 'info'):
                self.settings.remove('panels/' + mode + '/' + name)
        self.panel_layout_mode = None
        self.restore_workspace_panels(self.width() < 1300)

    def change_inline_theme(self,name):
        self.theme.setCurrentText(name)

    def apply_theme(self,*_):
        if not hasattr(self,'theme'):return
        accent=THEMES.get(self.theme.currentText(),THEMES['Neo Purple'])
        self.setStyleSheet(stylesheet(accent))
        self.inline_theme.blockSignals(True);self.inline_theme.setCurrentText(self.theme.currentText());self.inline_theme.blockSignals(False)
        self.rain.configure(accent,self.animation.isChecked() and not self.reduced.isChecked(),self.intensity.value(),self.speed.value())
        self.art_header.accent=accent;self.art_header.update()
        for item in self.findChildren(NeonPanel)+self.findChildren(NeonButton):
            item.accent=accent;item.glow=self.glow.isChecked();item.update()
        for key,value in [('theme',self.theme.currentText()),('matrix',self.animation.isChecked()),('glow',self.glow.isChecked()),('reduced',self.reduced.isChecked()),('intensity',self.intensity.value()),('speed',self.speed.value())]:self.settings.setValue(key,value)

    def reset_appearance(self):
        for item in [self.theme,self.animation,self.glow,self.reduced,self.intensity,self.speed]:item.blockSignals(True)
        self.theme.setCurrentText('Neo Purple');self.animation.setChecked(True);self.glow.setChecked(True);self.reduced.setChecked(False)
        self.intensity.setValue(85);self.speed.setValue(70)
        for item in [self.theme,self.animation,self.glow,self.reduced,self.intensity,self.speed]:item.blockSignals(False)
        self.apply_theme()

    def reflow(self):
        if not hasattr(self,'connection_grid'):return
        narrow=self.width()<1390
        while self.connection_grid.count():self.connection_grid.takeAt(0)
        for i,section in enumerate(self.connection_sections):self.connection_grid.addWidget(section,i//2 if narrow else 0,i%2 if narrow else i)
        while self.tab_grid.count():self.tab_grid.takeAt(0)
        tab_narrow=self.width()<1250
        for i,btn in enumerate(self.tab_buttons.values()):self.tab_grid.addWidget(btn,i//4 if tab_narrow else 0,i%4 if tab_narrow else i)
        self.foundation_button.setVisible(self.width()>=1200)
        if hasattr(self,'gpio_upper'):

            compact=self.width()<1300
            self.restore_workspace_panels(compact)
            self.gpio_toggles.setDirection(QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight)
            while self.gpio_controls.count():self.gpio_controls.takeAt(0)
            for column in range(6):self.gpio_controls.setColumnStretch(column,0)
            self.gpio_controls.addWidget(self.pin,0,0,1,3 if compact else 1)
            for i,btn in enumerate(self.gpio_buttons.values()):
                self.gpio_controls.addWidget(btn,1+i//3 if compact else 0,i%3 if compact else i+1)
            for column in range(3 if compact else 6):self.gpio_controls.setColumnStretch(column,1)
        # Settle changed splitter constraints before the scroll area uses its old width.
        self.content.layout().activate()
        QTimer.singleShot(0, self.settle_workspace_layout)
        scroll = self.stack.currentWidget()
        if scroll is not None:
            page = scroll.widget()
            page.layout().activate()
            page.resize(max(scroll.viewport().width(), page.minimumSizeHint().width()), page.height())


    def settle_workspace_layout(self):
        scroll = self.stack.currentWidget()
        if scroll is not None:
            page = scroll.widget()
            page.layout().activate()
            page.resize(max(scroll.viewport().width(), page.minimumSizeHint().width()), page.height())

    def closeEvent(self,event):
        super().closeEvent(event)
        if event.isAccepted():
            self.save_workspace_panels()
            self.settings.setValue("window_geometry",self.saveGeometry())
            self.settings.sync()

    def resizeEvent(self,event):
        super().resizeEvent(event);self.reflow()
