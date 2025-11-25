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


class SizeWidget(QWidget):
    size_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_w = 0
        self._original_h = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        size_row = QHBoxLayout()

        self._width_label = QLabel("너비")
        self._width_label.setFixedWidth(30)
        size_row.addWidget(self._width_label)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 10000)
        self._width_spin.setSuffix(" px")
        self._width_spin.valueChanged.connect(self._on_width_change)
        size_row.addWidget(self._width_spin)

        self._link_btn = QPushButton("🔗")
        self._link_btn.setCheckable(True)
        self._link_btn.setChecked(True)
        self._link_btn.setFixedSize(30, 30)
        self._link_btn.setToolTip("비율 유지")
        self._link_btn.toggled.connect(self._on_ratio_toggle)
        size_row.addWidget(self._link_btn)

        self._height_label = QLabel("높이")
        self._height_label.setFixedWidth(30)
        size_row.addWidget(self._height_label)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(1, 10000)
        self._height_spin.setSuffix(" px")
        self._height_spin.valueChanged.connect(self._on_height_change)
        size_row.addWidget(self._height_spin)

        layout.addLayout(size_row)

        reset_row = QHBoxLayout()
        self._reset_btn = QPushButton("원본 크기로 복원")
        self._reset_btn.clicked.connect(self._on_reset)
        reset_row.addWidget(self._reset_btn)
        layout.addLayout(reset_row)

    def _on_width_change(self, value: int):
        if self._link_btn.isChecked() and self._original_w > 0:
            ratio = value / self._original_w
            new_h = int(self._original_h * ratio)
            self._height_spin.blockSignals(True)
            self._height_spin.setValue(new_h)
            self._height_spin.blockSignals(False)

        self.size_changed.emit(self._width_spin.value(), self._height_spin.value())

    def _on_height_change(self, value: int):
        if self._link_btn.isChecked() and self._original_h > 0:
            ratio = value / self._original_h
            new_w = int(self._original_w * ratio)
            self._width_spin.blockSignals(True)
            self._width_spin.setValue(new_w)
            self._width_spin.blockSignals(False)

        self.size_changed.emit(self._width_spin.value(), self._height_spin.value())

    def _on_ratio_toggle(self, checked: bool):
        self._link_btn.setText("🔗" if checked else "🔓")

    def _on_reset(self):
        if self._original_w > 0 and self._original_h > 0:
            self.set_size(self._original_w, self._original_h)

    def set_original_size(self, w: int, h: int):
        self._original_w = w
        self._original_h = h

    def set_size(self, w: int, h: int):
        self._width_spin.blockSignals(True)
        self._height_spin.blockSignals(True)
        self._width_spin.setValue(w)
        self._height_spin.setValue(h)
        self._width_spin.blockSignals(False)
        self._height_spin.blockSignals(False)
        self.size_changed.emit(w, h)

    def get_size(self) -> tuple[int, int]:
        return self._width_spin.value(), self._height_spin.value()

    def is_ratio_locked(self) -> bool:
        return self._link_btn.isChecked()


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

        size_group = QGroupBox("크기 조절")
        size_layout = QVBoxLayout(size_group)
        self._size_widget = SizeWidget()
        size_layout.addWidget(self._size_widget)
        layout.addWidget(size_group)

        transform_group = QGroupBox("변환")
        transform_layout = QVBoxLayout(transform_group)

        self._rotation = RotationWidget()
        transform_layout.addWidget(self._rotation)
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

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _connect_signals(self):
        self._size_widget.size_changed.connect(self._emit_change)
        self._rotation.value_changed.connect(self._emit_change)
        self._brightness.value_changed.connect(self._emit_change)
        self._contrast.value_changed.connect(self._emit_change)
        self._saturation.value_changed.connect(self._emit_change)
        self._noise.value_changed.connect(self._emit_change)
        self._exif_panel.exif_changed.connect(self._emit_change)

    def _on_free_transform_toggle(self, checked: bool):
        self.free_transform_toggled.emit(checked)
        self._emit_change()

    def _emit_change(self, *args):
        self.options_changed.emit(self.get_options())

    def get_options(self) -> dict:
        w, h = self._size_widget.get_size()
        return {
            "width": w,
            "height": h,
            "keep_ratio": self._size_widget.is_ratio_locked(),
            "free_transform_mode": True,  # 항상 자유변형 모드
            "rotation": self._rotation.value(),
            "brightness": self._brightness.value(),
            "contrast": self._contrast.value(),
            "saturation": self._saturation.value(),
            "noise": self._noise.value(),
            "exif": self._exif_panel.get_exif_options(),
        }

    def set_options(self, options: dict):
        if "width" in options and "height" in options:
            self._size_widget.set_size(options["width"], options["height"])
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
        self._size_widget.set_original_size(w, h)
        self._size_widget.set_size(w, h)

    def set_size_from_preview(self, w: int, h: int):
        self._size_widget.set_size(w, h)
