from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal


class RotationWidget(QWidget):
    value_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("회전")
        self._label.setFixedWidth(60)
        layout.addWidget(self._label)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(-1800, 1800)
        self._slider.setValue(0)
        self._slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self._slider)

        self._spinbox = QDoubleSpinBox()
        self._spinbox.setRange(-180.0, 180.0)
        self._spinbox.setSingleStep(0.1)
        self._spinbox.setDecimals(1)
        self._spinbox.setValue(0.0)
        self._spinbox.setFixedWidth(70)
        self._spinbox.setSuffix("°")
        self._spinbox.valueChanged.connect(self._on_spinbox_change)
        layout.addWidget(self._spinbox)

    def _on_slider_change(self, value: int):
        float_value = value / 10.0
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(float_value)
        self._spinbox.blockSignals(False)
        self.value_changed.emit(float_value)

    def _on_spinbox_change(self, value: float):
        int_value = int(value * 10)
        self._slider.blockSignals(True)
        self._slider.setValue(int_value)
        self._slider.blockSignals(False)
        self.value_changed.emit(value)

    def value(self) -> float:
        return self._spinbox.value()

    def set_value(self, value: float):
        self._slider.blockSignals(True)
        self._spinbox.blockSignals(True)
        self._slider.setValue(int(value * 10))
        self._spinbox.setValue(value)
        self._slider.blockSignals(False)
        self._spinbox.blockSignals(False)
