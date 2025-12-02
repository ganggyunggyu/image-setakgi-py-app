from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QPen, QColor


class SpinnerWidget(QWidget):
    """회전 스피너"""

    def __init__(self, parent=None, size=48, color="#4285f4"):
        super().__init__(parent)
        self._size = size
        self._color = QColor(color)
        self._angle = 0
        self.setFixedSize(size, size)

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30fps
        self._timer.timeout.connect(self._rotate)

    def _rotate(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self._color)
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        margin = 6
        rect = QRectF(margin, margin, self._size - margin * 2, self._size - margin * 2)
        painter.drawArc(rect, self._angle * 16, 270 * 16)


class BusyOverlay(QWidget):
    """풀스크린 로딩 오버레이"""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 200);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._spinner = SpinnerWidget(self, size=48, color="#4285f4")
        layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel("처리 중")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            "color: #ffffff; font-size: 18px; font-weight: 500; background: transparent;"
        )
        layout.addWidget(self._title)

        self.hide()

    def show_message(self, title: str, subtitle: str = ""):
        self._title.setText(title)
        self._spinner.start()
        self.raise_()
        self.show()

    def hide_overlay(self):
        self._spinner.stop()
        self.hide()
