"""자유변형 안내 위젯"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal


class PerspectiveWidget(QWidget):
    """자유변형 안내 - 프리뷰에서 코너 드래그로 조작"""

    perspective_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel("💡 프리뷰에서 코너를 드래그하세요")
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

    def value(self) -> float:
        return 0.0

    def set_value(self, value: float):
        pass
