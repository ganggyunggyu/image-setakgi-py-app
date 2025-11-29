from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
)
from PySide6.QtCore import Signal

from app.core.random_config import (
    CROP_RANGE,
    ROTATION_RANGE,
    NOISE_RANGE,
    PERSPECTIVE_RANGE,
    DATE_DAYS_BACK,
)


class RandomConfigPanel(QWidget):
    """랜덤 변환 설정 패널"""

    config_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 크롭 범위
        crop_row = QHBoxLayout()
        crop_label = QLabel("크롭 범위")
        crop_label.setFixedWidth(80)
        crop_row.addWidget(crop_label)
        self._crop_spin = QDoubleSpinBox()
        self._crop_spin.setRange(0, 50)
        self._crop_spin.setValue(CROP_RANGE)
        self._crop_spin.setSuffix(" px")
        self._crop_spin.setDecimals(1)
        self._crop_spin.valueChanged.connect(self._on_change)
        crop_row.addWidget(self._crop_spin)
        crop_row.addStretch()
        layout.addLayout(crop_row)

        # 회전 범위
        rotation_row = QHBoxLayout()
        rotation_label = QLabel("회전 범위")
        rotation_label.setFixedWidth(80)
        rotation_row.addWidget(rotation_label)
        self._rotation_spin = QDoubleSpinBox()
        self._rotation_spin.setRange(0, 180)
        self._rotation_spin.setValue(ROTATION_RANGE)
        self._rotation_spin.setSuffix(" °")
        self._rotation_spin.setDecimals(1)
        self._rotation_spin.valueChanged.connect(self._on_change)
        rotation_row.addWidget(self._rotation_spin)
        rotation_row.addStretch()
        layout.addLayout(rotation_row)

        # 노이즈 범위
        noise_row = QHBoxLayout()
        noise_label = QLabel("노이즈 범위")
        noise_label.setFixedWidth(80)
        noise_row.addWidget(noise_label)
        self._noise_spin = QDoubleSpinBox()
        self._noise_spin.setRange(0, 50)
        self._noise_spin.setValue(NOISE_RANGE)
        self._noise_spin.setDecimals(1)
        self._noise_spin.valueChanged.connect(self._on_change)
        noise_row.addWidget(self._noise_spin)
        noise_row.addStretch()
        layout.addLayout(noise_row)

        # 자유변형 범위
        perspective_row = QHBoxLayout()
        perspective_label = QLabel("자유변형 범위")
        perspective_label.setFixedWidth(80)
        perspective_row.addWidget(perspective_label)
        self._perspective_spin = QDoubleSpinBox()
        self._perspective_spin.setRange(0, 20)
        self._perspective_spin.setValue(PERSPECTIVE_RANGE)
        self._perspective_spin.setSuffix(" px")
        self._perspective_spin.setDecimals(1)
        self._perspective_spin.valueChanged.connect(self._on_change)
        perspective_row.addWidget(self._perspective_spin)
        perspective_row.addStretch()
        layout.addLayout(perspective_row)

        # 날짜 범위
        date_row = QHBoxLayout()
        date_label = QLabel("날짜 범위")
        date_label.setFixedWidth(80)
        date_row.addWidget(date_label)
        self._date_spin = QSpinBox()
        self._date_spin.setRange(1, 365)
        self._date_spin.setValue(DATE_DAYS_BACK)
        self._date_spin.setSuffix(" 일")
        self._date_spin.valueChanged.connect(self._on_change)
        date_row.addWidget(self._date_spin)
        date_row.addStretch()
        layout.addLayout(date_row)

        # 기본값 복원 버튼
        reset_btn = QPushButton("기본값 복원")
        reset_btn.clicked.connect(self._reset_to_default)
        layout.addWidget(reset_btn)

    def _on_change(self):
        self.config_changed.emit(self.get_config())

    def _reset_to_default(self):
        self._crop_spin.setValue(CROP_RANGE)
        self._rotation_spin.setValue(ROTATION_RANGE)
        self._noise_spin.setValue(NOISE_RANGE)
        self._perspective_spin.setValue(PERSPECTIVE_RANGE)
        self._date_spin.setValue(DATE_DAYS_BACK)

    def get_config(self) -> dict:
        return {
            "crop_range": self._crop_spin.value(),
            "rotation_range": self._rotation_spin.value(),
            "noise_range": self._noise_spin.value(),
            "perspective_range": self._perspective_spin.value(),
            "date_days_back": self._date_spin.value(),
        }

    def set_config(self, config: dict):
        if "crop_range" in config:
            self._crop_spin.setValue(config["crop_range"])
        if "rotation_range" in config:
            self._rotation_spin.setValue(config["rotation_range"])
        if "noise_range" in config:
            self._noise_spin.setValue(config["noise_range"])
        if "perspective_range" in config:
            self._perspective_spin.setValue(config["perspective_range"])
        if "date_days_back" in config:
            self._date_spin.setValue(config["date_days_back"])
