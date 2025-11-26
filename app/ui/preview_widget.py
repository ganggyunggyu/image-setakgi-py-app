"""프리뷰 위젯 - 이미지 미리보기 및 크기 정보 표시"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from .graphics.view import PreviewGraphicsView


class PreviewWidget(QWidget):
    size_changed = Signal(int, int)
    perspective_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._title = QLabel("미리보기")
        self._title.setStyleSheet("font-weight: bold; color: #fff; padding: 5px;")
        layout.addWidget(self._title)

        self._view = PreviewGraphicsView()
        self._view.size_changed.connect(self.size_changed)
        self._view.perspective_changed.connect(self.perspective_changed)
        layout.addWidget(self._view)

        self._info_label = QLabel("이미지를 드래그하여 추가하세요")
        self._info_label.setStyleSheet("color: #888; padding: 5px;")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._info_label)

    def set_image(self, pixmap: QPixmap, reset_transform: bool = False):
        self._view.set_image(pixmap, reset_transform)
        if not pixmap.isNull():
            self._info_label.setText("")
        else:
            self._info_label.setText("이미지를 드래그하여 추가하세요")

    def set_keep_ratio(self, keep: bool):
        self._view.set_keep_ratio(keep)

    def set_free_transform_mode(self, enabled: bool):
        self._view.set_free_transform_mode(enabled)
        if enabled:
            self._title.setText("미리보기 - 자유변형 모드")
        else:
            self._title.setText("미리보기")

    def update_info(self, width: int, height: int):
        self._view.update_display_size(width, height)

    def set_rotation(self, angle: float, original_size: tuple[int, int]):
        self._view.set_rotation(angle, original_size)
