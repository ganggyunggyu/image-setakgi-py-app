from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QFrame,
)
from PySide6.QtCore import Signal


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
