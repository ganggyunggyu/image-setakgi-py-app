from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QComboBox,
)
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


class RandomConfigPanel(QWidget):
    """랜덤 변환 설정 패널"""
    config_changed = Signal(dict)

    # 기본값 (random_config.py와 동일)
    DEFAULT_CROP_RANGE = 6.0
    DEFAULT_ROTATION_RANGE = 3.0
    DEFAULT_NOISE_RANGE = 4.0
    DEFAULT_PERSPECTIVE_RANGE = 1.6
    DEFAULT_DATE_DAYS_BACK = 7

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
        self._crop_spin.setValue(self.DEFAULT_CROP_RANGE)
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
        self._rotation_spin.setValue(self.DEFAULT_ROTATION_RANGE)
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
        self._noise_spin.setValue(self.DEFAULT_NOISE_RANGE)
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
        self._perspective_spin.setValue(self.DEFAULT_PERSPECTIVE_RANGE)
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
        self._date_spin.setValue(self.DEFAULT_DATE_DAYS_BACK)
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
        self._crop_spin.setValue(self.DEFAULT_CROP_RANGE)
        self._rotation_spin.setValue(self.DEFAULT_ROTATION_RANGE)
        self._noise_spin.setValue(self.DEFAULT_NOISE_RANGE)
        self._perspective_spin.setValue(self.DEFAULT_PERSPECTIVE_RANGE)
        self._date_spin.setValue(self.DEFAULT_DATE_DAYS_BACK)

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


class ExifPanel(QWidget):
    exif_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._remove_check = QCheckBox("EXIF 전체 삭제")
        self._remove_check.toggled.connect(self._on_change)
        layout.addWidget(self._remove_check)

        self._override_check = QCheckBox("EXIF 덮어쓰기")
        self._override_check.toggled.connect(self._toggle_override_fields)
        layout.addWidget(self._override_check)

        self._override_frame = QFrame()
        self._override_frame.setVisible(False)
        override_layout = QVBoxLayout(self._override_frame)

        self._make_input = QLineEdit()
        self._make_input.setPlaceholderText("제조사 (예: Canon)")
        self._make_input.textChanged.connect(self._on_change)
        override_layout.addWidget(self._make_input)

        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("모델명 (예: EOS 5D)")
        self._model_input.textChanged.connect(self._on_change)
        override_layout.addWidget(self._model_input)

        self._datetime_input = QLineEdit()
        self._datetime_input.setPlaceholderText("촬영일시 (예: 2024:01:01 12:00:00)")
        self._datetime_input.textChanged.connect(self._on_change)
        override_layout.addWidget(self._datetime_input)

        self._random_btn = QPushButton("랜덤 EXIF 생성")
        self._random_btn.clicked.connect(self._generate_random)
        override_layout.addWidget(self._random_btn)

        layout.addWidget(self._override_frame)

    def _toggle_override_fields(self, checked: bool):
        self._override_frame.setVisible(checked)
        if checked:
            self._remove_check.setChecked(False)
        self._on_change()

    def _on_change(self):
        self.exif_changed.emit(self.get_exif_options())

    def _generate_random(self):
        from app.core.metadata import generate_random_exif

        random_exif = generate_random_exif()
        self._make_input.setText(random_exif.get("Make", ""))
        self._model_input.setText(random_exif.get("Model", ""))
        self._datetime_input.setText(random_exif.get("DateTimeOriginal", ""))

    def get_exif_options(self) -> dict:
        return {
            "remove_all": self._remove_check.isChecked(),
            "override": self._override_check.isChecked(),
            "make": self._make_input.text(),
            "model": self._model_input.text(),
            "datetime": self._datetime_input.text(),
        }

    def set_exif_options(self, options: dict):
        self._remove_check.setChecked(options.get("remove_all", False))
        self._override_check.setChecked(options.get("override", False))
        self._make_input.setText(options.get("make", ""))
        self._model_input.setText(options.get("model", ""))
        self._datetime_input.setText(options.get("datetime", ""))


class OptionsPanel(QWidget):
    options_changed = Signal(dict)
    free_transform_toggled = Signal(bool)
    reset_requested = Signal()
    perspective_offset_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        # 자유변형 모드 항상 활성화
        self.free_transform_toggled.emit(True)

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)

        random_group = QGroupBox("랜덤 변환 설정")
        random_layout = QVBoxLayout(random_group)
        self._random_config = RandomConfigPanel()
        random_layout.addWidget(self._random_config)
        layout.addWidget(random_group)

        crop_group = QGroupBox("테두리 크롭")
        crop_layout = QVBoxLayout(crop_group)
        self._crop_widget = CropWidget()
        crop_layout.addWidget(self._crop_widget)
        layout.addWidget(crop_group)

        transform_group = QGroupBox("변환")
        transform_layout = QVBoxLayout(transform_group)

        self._rotation = RotationWidget()
        transform_layout.addWidget(self._rotation)

        self._perspective = PerspectiveWidget()
        transform_layout.addWidget(self._perspective)

        layout.addWidget(transform_group)

        adjust_group = QGroupBox("색상 조정")
        adjust_layout = QVBoxLayout(adjust_group)
        self._brightness = SliderWithSpinBox("밝기", -100, 100, 0)
        self._contrast = SliderWithSpinBox("대비", -100, 100, 0)
        self._saturation = SliderWithSpinBox("채도", -100, 100, 0)
        adjust_layout.addWidget(self._brightness)
        adjust_layout.addWidget(self._contrast)
        adjust_layout.addWidget(self._saturation)
        layout.addWidget(adjust_group)

        noise_group = QGroupBox("노이즈")
        noise_layout = QVBoxLayout(noise_group)
        self._noise = SliderWithSpinBox("강도", 0, 100, 0)
        noise_layout.addWidget(self._noise)
        layout.addWidget(noise_group)

        exif_group = QGroupBox("EXIF 메타데이터")
        exif_layout = QVBoxLayout(exif_group)
        self._exif_panel = ExifPanel()
        exif_layout.addWidget(self._exif_panel)
        layout.addWidget(exif_group)

        layout.addStretch()

        reset_all_btn = QPushButton("전체 초기화")
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5252;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff1744;
            }
        """)
        reset_all_btn.clicked.connect(self._reset_all_options)
        layout.addWidget(reset_all_btn)

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _connect_signals(self):
        self._crop_widget.crop_changed.connect(self._emit_change)
        self._rotation.value_changed.connect(self._emit_change)
        self._perspective.perspective_changed.connect(self._on_perspective_change)
        self._brightness.value_changed.connect(self._emit_change)
        self._contrast.value_changed.connect(self._emit_change)
        self._saturation.value_changed.connect(self._emit_change)
        self._noise.value_changed.connect(self._emit_change)
        self._exif_panel.exif_changed.connect(self._emit_change)

    def _on_perspective_change(self, offset: float):
        self.perspective_offset_changed.emit(offset)
        self._emit_change()

    def _on_free_transform_toggle(self, checked: bool):
        self.free_transform_toggled.emit(checked)
        self._emit_change()

    def _emit_change(self, *args):
        self.options_changed.emit(self.get_options())

    def _reset_all_options(self):
        self._crop_widget._on_reset()
        self._rotation.set_value(0.0)
        self._perspective.set_value(0.0)
        self._brightness.set_value(0)
        self._contrast.set_value(0)
        self._saturation.set_value(0)
        self._noise.set_value(0)
        self._exif_panel.set_exif_options({
            "remove_all": False,
            "override": False,
            "make": "",
            "model": "",
            "datetime": "",
        })
        self.reset_requested.emit()

    def get_options(self) -> dict:
        w, h = self._crop_widget.get_output_size()
        crop = self._crop_widget.get_crop()
        return {
            "width": w,
            "height": h,
            "crop": crop,
            "free_transform_mode": True,
            "rotation": self._rotation.value(),
            "perspective_offset": self._perspective.value(),
            "brightness": self._brightness.value(),
            "contrast": self._contrast.value(),
            "saturation": self._saturation.value(),
            "noise": self._noise.value(),
            "exif": self._exif_panel.get_exif_options(),
        }

    def set_options(self, options: dict):
        if "crop" in options:
            self._crop_widget.set_crop(options["crop"])
        if "rotation" in options:
            self._rotation.set_value(options["rotation"])
        if "brightness" in options:
            self._brightness.set_value(options["brightness"])
        if "contrast" in options:
            self._contrast.set_value(options["contrast"])
        if "saturation" in options:
            self._saturation.set_value(options["saturation"])
        if "noise" in options:
            self._noise.set_value(options["noise"])
        if "exif" in options:
            self._exif_panel.set_exif_options(options["exif"])

    def set_original_size(self, w: int, h: int):
        self._crop_widget.set_original_size(w, h)
        self._crop_widget._on_reset()

    def get_random_config(self) -> dict:
        """랜덤 변환 설정값 반환"""
        return self._random_config.get_config()
