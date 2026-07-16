"""A small, painted audio-wave animation without external assets."""

import math

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ProgressAnimation(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(92)
        self._tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(55)

    def _advance(self) -> None:
        self._tick += 1
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        center = height / 2
        count = 19
        gap = width / (count + 1)
        for index in range(count):
            phase = self._tick / 8 + index * 0.58
            bar_height = 18 + (math.sin(phase) + 1) * 20
            alpha = 105 + int((math.sin(phase + 0.7) + 1) * 55)
            color = QColor(23, 144, 128, alpha)
            painter.setPen(QPen(color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            x = gap * (index + 1)
            painter.drawLine(int(x), int(center - bar_height / 2), int(x), int(center + bar_height / 2))
