from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QSpinBox
from PySide6.QtCore import Qt, Signal


class SliderWithSpinBox(QWidget):
    value_changed = Signal(int)

    def __init__(
        self,
        label: str,
        min_val: int,
        max_val: int,
        default: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self._setup_ui(label, min_val, max_val, default)

    def _setup_ui(self, label: str, min_val: int, max_val: int, default: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._label.setFixedWidth(60)
        layout.addWidget(self._label)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(min_val, max_val)
        self._slider.setValue(default)
        self._slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self._slider)

        self._spinbox = QSpinBox()
        self._spinbox.setRange(min_val, max_val)
        self._spinbox.setValue(default)
        self._spinbox.setFixedWidth(70)
        self._spinbox.valueChanged.connect(self._on_spinbox_change)
        layout.addWidget(self._spinbox)

    def _on_slider_change(self, value: int):
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(value)
        self._spinbox.blockSignals(False)
        self.value_changed.emit(value)

    def _on_spinbox_change(self, value: int):
        self._slider.blockSignals(True)
        self._slider.setValue(value)
        self._slider.blockSignals(False)
        self.value_changed.emit(value)

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, value: int):
        self._slider.blockSignals(True)
        self._spinbox.blockSignals(True)
        self._slider.setValue(value)
        self._spinbox.setValue(value)
        self._slider.blockSignals(False)
        self._spinbox.blockSignals(False)
