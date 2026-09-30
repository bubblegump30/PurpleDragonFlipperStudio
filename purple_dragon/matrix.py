"""Resolution-independent, bounded Matrix rain, with a single animation timer."""
import random
from PySide6.QtCore import QTimer, QElapsedTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class MatrixRain(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.color = QColor('#9256ff')
        self.intensity, self.speed = 32, 55
        self.enabled = True
        self.columns = []
        self.clock = QElapsedTimer()
        self.clock.start()
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def configure(self, color, enabled, intensity, speed):
        self.color = QColor(color)
        self.enabled, self.intensity, self.speed = enabled, intensity, speed
        self.set_running(enabled and self.isVisible())
        self.update()

    def set_running(self, running):
        if running and self.enabled:
            self.clock.restart()
            self.timer.start()
        else:
            self.timer.stop()

    def resizeEvent(self, event):
        count = min(120, max(1, self.width() // 26))
        self.columns = [[random.uniform(-self.height(), self.height()), random.uniform(.6, 1.5), ''.join(random.choices('01ABCDEF<>:+=', k=27))] for _ in range(count)]
        super().resizeEvent(event)

    def tick(self):
        dt = min(self.clock.restart()/1000, .15)
        for col in self.columns:
            col[0] += self.speed * col[1] * dt
            if col[0] - 180 > self.height():
                col[0] = random.uniform(-300, -20)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#090b12'))
        grid = QColor(self.color)
        grid.setAlpha(13)
        p.setPen(QPen(grid, 1))
        for x in range(0, self.width(), 64):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 64):
            p.drawLine(0, y, self.width(), y)
        if not self.enabled:
            return
        p.setFont(QFont('Consolas', 9))
        for i, (y, _, chars) in enumerate(self.columns):
            x = int(i * self.width() / max(1, len(self.columns)))
            for j, char in enumerate(chars):
                shade = QColor(self.color)
                shade.setAlpha(min(230,int(self.intensity * 1.65 * (1-j/len(chars)))))
                p.setPen(shade)
                p.drawText(x, int(y-j*17), char)
