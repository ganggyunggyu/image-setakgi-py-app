from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PySide6.QtCore import Signal


class OutputFormatPanel(QWidget):
    """출력 포맷 선택 패널"""

    format_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("출력 포맷")
        label.setFixedWidth(70)
        layout.addWidget(label)

        self._combo = QComboBox()
        self._combo.addItem("JPEG (.jpg)", "jpeg")
        self._combo.addItem("WebP (.webp)", "webp")
        self._combo.setCurrentIndex(0)
        self._combo.currentIndexChanged.connect(self._on_change)
        layout.addWidget(self._combo)

        layout.addStretch()

    def _on_change(self, index: int):
        format_type = self._combo.currentData()
        self.format_changed.emit(format_type)

    def get_format(self) -> str:
        return self._combo.currentData()

    def set_format(self, format_type: str):
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == format_type:
                self._combo.setCurrentIndex(i)
                break
