from PIL import Image
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from typing import Optional
import io

from .image_ops import apply_transforms

MAX_PREVIEW_SIZE = 512


def create_thumbnail(img: Image.Image, max_size: int = MAX_PREVIEW_SIZE) -> Image.Image:
    w, h = img.size
    if w <= max_size and h <= max_size:
        return img.copy()

    ratio = min(max_size / w, max_size / h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode == "RGBA":
        qformat = QImage.Format.Format_RGBA8888
    else:
        img = img.convert("RGB")
        qformat = QImage.Format.Format_RGB888

    data = img.tobytes("raw", img.mode)
    qimage = QImage(data, img.width, img.height, qformat)
    return QPixmap.fromImage(qimage.copy())


class PreviewWorker(QObject):
    finished = Signal(QPixmap)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._img: Optional[Image.Image] = None
        self._options: dict = {}

    def set_source(self, img: Image.Image):
        self._img = create_thumbnail(img)

    def set_options(self, options: dict):
        self._options = options.copy()

    def process(self):
        if self._img is None:
            self.error.emit("No image loaded")
            return

        try:
            preview_w = self._options.get("width")
            preview_h = self._options.get("height")
            orig_w, orig_h = self._img.size

            if preview_w and preview_h:
                scale = min(MAX_PREVIEW_SIZE / preview_w, MAX_PREVIEW_SIZE / preview_h, 1)
                preview_w = int(preview_w * scale)
                preview_h = int(preview_h * scale)
            else:
                preview_w = None
                preview_h = None

            result = apply_transforms(
                self._img,
                width=preview_w,
                height=preview_h,
                keep_ratio=self._options.get("keep_ratio", True),
                rotation=self._options.get("rotation", 0),
                brightness=self._options.get("brightness", 0),
                contrast=self._options.get("contrast", 0),
                saturation=self._options.get("saturation", 0),
                noise=self._options.get("noise", 0),
            )

            pixmap = pil_to_qpixmap(result)
            self.finished.emit(pixmap)

        except Exception as e:
            self.error.emit(str(e))


class PreviewThread(QThread):
    preview_ready = Signal(QPixmap)
    preview_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = PreviewWorker()
        self._worker.finished.connect(self.preview_ready)
        self._worker.error.connect(self.preview_error)

    def set_source(self, img: Image.Image):
        self._worker.set_source(img)

    def set_options(self, options: dict):
        self._worker.set_options(options)

    def run(self):
        self._worker.process()
