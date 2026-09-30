"""Painted neon controls, vector icons, and artwork from the user's reference."""
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QByteArray, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QLinearGradient, QFont, QPixmap, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QVBoxLayout, QLabel

from . import __version__

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
PATHS = {
    'home':'M3 11L12 3l9 8 M6 10v11h12V10 M10 21v-7h4v7',
    'cpu':'M6 6h12v12H6z M9 2v4 M15 2v4 M9 18v4 M15 18v4 M2 9h4 M2 15h4 M18 9h4 M18 15h4',
    'terminal':'M3 4h18v16H3z M6 8l4 4-4 4 M12 16h5',
    'cube':'M12 2l9 5v10l-9 5-9-5V7z M3 7l9 5 9-5 M12 12v10',
    'gauge':'M4 19a10 10 0 1 1 16 0 M12 12l5-5 M6 10l-2-1 M12 3v3 M20 10l-2 1',
    'radio':'M5 5a10 10 0 0 0 0 14 M19 5a10 10 0 0 1 0 14 M8 8a6 6 0 0 0 0 8 M16 8a6 6 0 0 1 0 8 M12 12v9 M10 12a2 2 0 1 0 4 0a2 2 0 1 0-4 0',
    'folder':'M2 6h8l2 3h10v12H2z M2 6V3h7l3 3h10v3',
    'list':'M5 2h14v20H5z M8 6h8 M8 10h8 M8 14h8 M8 18h5',
    'globe':'M2 12h20 M12 2v20 M2 12a10 10 0 1 0 20 0a10 10 0 1 0-20 0 M12 2c-7 6-7 14 0 20 M12 2c7 6 7 14 0 20',
    'settings':'M9 3h6l1 4 4 1v8l-4 1-1 4H9l-1-4-4-1V8l4-1z M9 12a3 3 0 1 0 6 0a3 3 0 1 0-6 0',
    'palette':'M12 2a10 10 0 1 0 0 20h2l1-3-2-2 1-2h4c5 0 5-13-6-13 M6 8h1 M10 5h1 M15 6h1 M18 10h1',
    'info':'M2 12a10 10 0 1 0 20 0a10 10 0 1 0-20 0 M12 10v7 M12 6v1',
    'refresh':'M20 8a9 9 0 0 0-16-2 M4 6V2 M4 6h5 M4 16a9 9 0 0 0 16 2 M20 18v4 M20 18h-5',
    'plug':'M8 2v6 M16 2v6 M6 8h12v5l-6 5-6-5z M12 18v4',
    'save':'M3 3h15l3 3v15H3z M7 3v6h9V3 M7 21v-8h10v8',
    'trash':'M4 6h16 M9 3h6 M6 6l1 15h10l1-15 M10 10v7 M14 10v7',
    'search':'M3 10a7 7 0 1 0 14 0a7 7 0 1 0-14 0 M15 15l7 7',
    'down':'M12 3v17 M6 14l6 6 6-6', 'up':'M12 21V4 M6 10l6-6 6 6',
    'input':'M3 12h14 M12 7l5 5-5 5 M18 4h4v16h-4',
    'output':'M21 12H7 M12 7l-5 5 5 5 M6 4H2v16h4',
    'pulse':'M2 12h5l3-8 4 16 3-8h5', 'export':'M3 14v7h18v-7 M12 17V2 M6 8l6-6 6 6',
}


def icon(name, color='#cbb9ff'):
    path = PATHS.get(name, PATHS['cpu'])
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="{path}" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pix = QPixmap(64,64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return QIcon(pix)


def glow_path(p, path, color, strength=1):
    for width, alpha in [(15,10),(10,20),(6,38),(3,75),(1.2,210)]:
        shade=QColor(color);shade.setAlpha(int(alpha*strength))
        p.setPen(QPen(shade,width));p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path)


class NeonPanel(QFrame):
    def __init__(self, parent=None, tone='blue'):
        super().__init__(parent)
        self.tone=tone
        self.accent='#b000ff'
        self.glow=True
        self.setObjectName('neonPanel')

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect=QRectF(self.rect()).adjusted(5,5,-5,-5)
        path=QPainterPath();path.addRoundedRect(rect,12,12)
        color=self.accent if self.tone=='accent' else '#247eb0'
        grad=QLinearGradient(rect.topLeft(),rect.bottomRight())
        grad.setColorAt(0,QColor(4,15,28,241));grad.setColorAt(.6,QColor(2,7,18,237));grad.setColorAt(1,QColor(9,5,25,240))
        p.fillPath(path,grad)
        glow_path(p,path,color,1 if self.glow and self.tone=='accent' else .48)
        p.setPen(QPen(QColor('#24445d'),.7));p.drawLine(int(rect.left()+14),int(rect.top()+2),int(rect.right()-14),int(rect.top()+2))


def panel(title=None):
    item=NeonPanel()
    layout=QVBoxLayout(item);layout.setContentsMargins(18,16,18,16);layout.setSpacing(12)
    if title:
        text=QLabel(title);text.setObjectName('sectionTitle');layout.addWidget(text)
    return item,layout


class NeonButton(QPushButton):
    def __init__(self,text,callback=None,role='neutral',glyph=None,parent=None):
        super().__init__(text,parent)
        self.role=role;self.glyph=glyph;self.accent='#b000ff';self.glow=True
        self.compact=False
        self.keyboard_focus=False
        self.setToolTip(text.replace("&&", "&").replace("\n", " "))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setMinimumWidth(70)
        if callback:self.clicked.connect(callback)

    def sizeHint(self):
        if self.role=='nav':return QSize(160,54)
        return QSize(max(96,super().sizeHint().width()+45),46)

    def focusInEvent(self,event):
        self.keyboard_focus=event.reason() in (Qt.FocusReason.TabFocusReason,Qt.FocusReason.BacktabFocusReason,Qt.FocusReason.ShortcutFocusReason)
        super().focusInEvent(event)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect=QRectF(self.rect()).adjusted(5,5,-5,-5)
        nav=self.role=='nav';active=self.isChecked()
        hue={'primary':self.accent,'purple':self.accent,'cyan':'#00efdb','blue':'#008dff','red':'#ff206e','neutral':'#677daf','nav':self.accent}.get(self.role,self.accent)
        if not self.isEnabled() and self.role=='primary':hue=self.accent
        path=QPainterPath();path.addRoundedRect(rect,6 if nav else 7,6 if nav else 7)
        if nav and not active and not self.underMouse():
            p.fillPath(path,QColor(4,10,22,30))
        else:
            grad=QLinearGradient(rect.topLeft(),rect.bottomLeft())
            color=QColor(hue)
            vivid=self.role in ('primary','purple','cyan','blue','red') or active
            if vivid:
                top=QColor(color);top.setAlpha(130 if not self.isDown() else 70)
                bottom=QColor(color.darker(330));bottom.setAlpha(235)
            else:top=QColor('#1d2942');bottom=QColor('#09101e')
            grad.setColorAt(0,top);grad.setColorAt(.42,bottom);grad.setColorAt(1,QColor('#080b1b'))
            p.fillPath(path,grad)
            if self.glow:glow_path(p,path,hue,(.85 if vivid else .2) * (1 if self.isEnabled() else .32))
            else:p.setPen(QPen(QColor(hue),1));p.drawPath(path)
            line=QColor(hue);line.setAlpha(190 if vivid else 70);p.setPen(QPen(line,.8));p.drawLine(int(rect.left()+8),int(rect.top()+2),int(rect.right()-8),int(rect.top()+2))
        if nav and active:
            p.setPen(QPen(QColor(self.accent),3));p.drawLine(7,10,7,self.height()-10)
        textcolor='#f7eaff' if active or self.role in ('primary','purple') else '#d6e2ff'
        if self.role=='cyan':textcolor='#6dfff1'
        if self.role=='red':textcolor='#ff8ec1'
        if not self.isEnabled():textcolor='#a5aec2'
        p.setPen(QColor(textcolor))
        font=QFont('Segoe UI',9 if self.compact else 10);font.setWeight(QFont.Weight.DemiBold if not nav else QFont.Weight.Normal);p.setFont(font)
        txt=self.text().replace('&&','&')
        if self.glyph:
            size=23 if nav else 20;x=18 if nav else max(14,int((self.width()-p.fontMetrics().horizontalAdvance(txt)-32)/2))
            if self.compact:size=20;x=12
            icon(self.glyph,textcolor).paint(p,x,(self.height()-size)//2,size,size)
            area=QRectF(x+size+11,0,self.width()-x-size-15,self.height())
            p.drawText(area,Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft|Qt.TextFlag.TextWordWrap,txt)
        else:p.drawText(rect,Qt.AlignmentFlag.AlignCenter,txt)
        if self.hasFocus() and self.keyboard_focus:
            p.setPen(QPen(QColor('#ffffff'),1,Qt.PenStyle.DotLine));p.drawRoundedRect(rect.adjusted(3,3,-3,-3),5,5)


def button(text,callback,primary=False):
    clean=text.replace('↗','').replace('→','').strip()
    return NeonButton(clean,callback,'primary' if primary else 'neutral')


class HeaderArt(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setFixedHeight(160)
        self.source=QPixmap(str(ASSETS/'design-reference.png'))
        self.accent='#b000ff'

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        width=self.width()
        dragon_width=175 if width>1100 else 135
        p.drawPixmap(QRectF(0,0,dragon_width,158),self.source,QRectF(174,40,197,163))
        text_x=dragon_width+12
        p.drawPixmap(QRectF(text_x,15,455,53),self.source,QRectF(369,54,482,55))
        p.drawPixmap(QRectF(text_x,73,455,42),self.source,QRectF(372,111,459,44))
        p.setFont(QFont('Segoe UI',10));p.setPen(QColor('#79e9ff'))
        p.drawText(text_x,130,'Flipper Zero companion  •  Official firmware  •  GUI v'+__version__)
        if width>1390:
            p.drawPixmap(QRectF(width-390,14,382,138),self.source,QRectF(1262,60,387,140))
        if width>1000:
            pos=width-745 if width>1390 else width-335
            p.drawPixmap(QRectF(pos,1,325,157),self.source,QRectF(914,45,335,157))


class ChipArt(QWidget):
    def __init__(self,parent=None,kind='purple'):
        super().__init__(parent);self.kind=kind;self.source=QPixmap(str(ASSETS/'design-reference.png'))
        self.setMinimumSize(130,95)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        src=QRectF(1190,404,443,77) if self.kind=='purple' else QRectF(1400,651,238,165)
        p.drawPixmap(QRectF(self.rect()),self.source,src)
        fade=QLinearGradient(0,0,self.width()*.5,0);fade.setColorAt(0,QColor('#040b18'));fade.setColorAt(1,QColor(4,11,24,0));p.fillRect(self.rect(),fade)
