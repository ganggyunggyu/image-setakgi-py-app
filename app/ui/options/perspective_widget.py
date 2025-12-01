from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
)
from PySide6.QtCore import Signal


class PerspectiveWidget(QWidget):
    """자유변형 오프셋 수동 조절 위젯"""

    perspective_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel("코너 오프셋")
        label.setFixedWidth(70)
        row.addWidget(label)

        self._spin = QDoubleSpinBox()
        self._spin.setRange(-50.0, 50.0)
        self._spin.setValue(0.0)
        self._spin.setSingleStep(0.5)
        self._spin.setDecimals(1)
        self._spin.setSuffix(" px")
        self._spin.setFixedWidth(100)
        self._spin.valueChanged.connect(self._on_spin_change)
        row.addWidget(self._spin)

        row.addStretch()
        layout.addLayout(row)

        info_label = QLabel("4개 코너에 ±오프셋 적용")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info_label)

        reset_row = QHBoxLayout()
        self._reset_btn = QPushButton("자유변형 초기화")
        self._reset_btn.clicked.connect(self._on_reset)
        reset_row.addWidget(self._reset_btn)
        layout.addLayout(reset_row)

    def _on_spin_change(self, value: float):
        self._offset = value
        self.perspective_changed.emit(value)

    def _on_reset(self):
        self._offset = 0.0
        self._spin.blockSignals(True)
        self._spin.setValue(0.0)
        self._spin.blockSignals(False)
        self.perspective_changed.emit(0.0)

    def value(self) -> float:
        return self._offset

    def set_value(self, value: float):
        self._offset = value
        self._spin.blockSignals(True)
        self._spin.setValue(value)
        self._spin.blockSignals(False)
