from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
)
from PySide6.QtCore import Signal


class CropWidget(QWidget):
    crop_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_w = 0
        self._original_h = 0
        self._crop_amount = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        crop_row = QHBoxLayout()
        crop_row.setSpacing(8)

        label = QLabel("테두리 크롭")
        label.setFixedWidth(70)
        crop_row.addWidget(label)

        self._spin = QSpinBox()
        self._spin.setRange(-500, 500)
        self._spin.setValue(0)
        self._spin.setSuffix(" px")
        self._spin.setFixedWidth(100)
        self._spin.valueChanged.connect(self._on_spin_change)
        crop_row.addWidget(self._spin)

        crop_row.addStretch()
        layout.addLayout(crop_row)

        size_row = QHBoxLayout()
        self._size_label = QLabel("출력: 0 x 0")
        self._size_label.setStyleSheet("color: #888; font-size: 11px;")
        size_row.addWidget(self._size_label)
        size_row.addStretch()
        layout.addLayout(size_row)

        reset_row = QHBoxLayout()
        self._reset_btn = QPushButton("크롭 초기화")
        self._reset_btn.clicked.connect(self._on_reset)
        reset_row.addWidget(self._reset_btn)
        layout.addLayout(reset_row)

    def _adjust_crop(self, delta: int):
        new_val = self._crop_amount + delta
        self._crop_amount = new_val
        self._spin.blockSignals(True)
        self._spin.setValue(new_val)
        self._spin.blockSignals(False)
        self._update_size_label()
        self.crop_changed.emit(self._get_crop_dict())

    def _on_spin_change(self, value: int):
        self._crop_amount = value
        self._update_size_label()
        self.crop_changed.emit(self._get_crop_dict())

    def _get_crop_dict(self) -> dict:
        return {
            "top": self._crop_amount,
            "bottom": self._crop_amount,
            "left": self._crop_amount,
            "right": self._crop_amount,
        }

    def _update_size_label(self):
        if self._original_w > 0 and self._original_h > 0:
            out_w = max(2, self._original_w - self._crop_amount * 2)
            out_h = max(2, self._original_h - self._crop_amount * 2)
            if out_w % 2 == 1:
                out_w += 1 if self._crop_amount < 0 else -1
            if out_h % 2 == 1:
                out_h += 1 if self._crop_amount < 0 else -1
            self._size_label.setText(f"출력: {out_w} x {out_h}")

    def _on_reset(self):
        self._crop_amount = 0
        self._spin.blockSignals(True)
        self._spin.setValue(0)
        self._spin.blockSignals(False)
        self._update_size_label()
        self.crop_changed.emit(self._get_crop_dict())

    def set_original_size(self, w: int, h: int):
        self._original_w = w
        self._original_h = h
        self._update_size_label()

    def get_crop(self) -> dict:
        return self._get_crop_dict()

    def set_crop(self, crop: dict):
        self._crop_amount = crop.get("top", 0)
        self._spin.blockSignals(True)
        self._spin.setValue(self._crop_amount)
        self._spin.blockSignals(False)
        self._update_size_label()

    def get_output_size(self) -> tuple[int, int]:
        out_w = max(2, self._original_w - self._crop_amount * 2)
        out_h = max(2, self._original_h - self._crop_amount * 2)
        if out_w % 2 == 1:
            out_w += 1 if self._crop_amount < 0 else -1
        if out_h % 2 == 1:
            out_h += 1 if self._crop_amount < 0 else -1
        return out_w, out_h
