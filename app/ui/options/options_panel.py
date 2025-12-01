from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from .slider_spinbox import SliderWithSpinBox
from .rotation_widget import RotationWidget
from .crop_widget import CropWidget
from .perspective_widget import PerspectiveWidget
from .random_config_panel import RandomConfigPanel
from .output_format_panel import OutputFormatPanel
from .exif_panel import ExifPanel


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

        output_group = QGroupBox("출력 설정")
        output_layout = QVBoxLayout(output_group)
        self._output_format = OutputFormatPanel()
        output_layout.addWidget(self._output_format)
        layout.addWidget(output_group)

        exif_group = QGroupBox("EXIF 메타데이터")
        exif_layout = QVBoxLayout(exif_group)
        self._exif_panel = ExifPanel()
        exif_layout.addWidget(self._exif_panel)
        layout.addWidget(exif_group)

        layout.addStretch()

        reset_all_btn = QPushButton("전체 초기화")
        reset_all_btn.setStyleSheet(
            """
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
        """
        )
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
        self._output_format.format_changed.connect(self._emit_change)
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
        self._exif_panel.set_exif_options(
            {
                "remove_all": False,
                "override": False,
                "make": "",
                "model": "",
                "datetime": "",
            }
        )
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
            "output_format": self._output_format.get_format(),
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
