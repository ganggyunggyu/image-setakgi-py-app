from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QRunnable, Signal
from PIL import Image, ImageOps

from app.core.preview import create_thumbnail, MAX_PREVIEW_SIZE
from app.core.image_ops import apply_transforms
from app.core.metadata import remove_exif
from app.core.transform_history import record_transform
from app.core.save_output import OutputManager


class WorkerSignals(QObject):
    progress = Signal(int, int)
    finished = Signal(str, bool, str, dict)  # filepath, success, result, applied_options
    all_done = Signal()


class TransformWorker(QRunnable):
    def __init__(
        self,
        filepath: str,
        options: dict,
        output_manager: OutputManager,
    ):
        super().__init__()
        self.filepath = filepath
        self.options = options
        self.output_manager = output_manager
        self.signals = WorkerSignals()

    def run(self):
        try:
            img = Image.open(self.filepath)

            # EXIF Orientation 태그에 따라 이미지 자동 회전
            img = ImageOps.exif_transpose(img) if img else img

            perspective_corners: Optional[list] = None
            if self.options.get("perspective_corners"):
                thumbnail = create_thumbnail(img, MAX_PREVIEW_SIZE)
                thumb_w, thumb_h = thumbnail.size
                orig_w, orig_h = img.size

                scale_x = orig_w / thumb_w
                scale_y = orig_h / thumb_h

                preview_corners = self.options.get("perspective_corners")
                perspective_corners = [
                    (x * scale_x, y * scale_y) for x, y in preview_corners
                ]

            result = apply_transforms(
                img,
                rotation=self.options.get("rotation", 0),
                brightness=self.options.get("brightness", 0),
                contrast=self.options.get("contrast", 0),
                saturation=self.options.get("saturation", 0),
                noise=self.options.get("noise", 0),
                perspective_corners=perspective_corners,
                crop=self.options.get("crop"),
            )

            # JPEG EXIF 메타데이터 처리 (DateTimeOriginal = Windows 촬영날짜)
            exif_opts = self.options.get("exif", {})
            metadata_overrides = None

            if exif_opts.get("remove_all"):
                result = remove_exif(result)
            elif exif_opts.get("override"):
                # datetime이 없으면 현재 시간 사용
                from datetime import datetime as dt

                datetime_val = exif_opts.get("datetime", "")
                if not datetime_val:
                    datetime_val = dt.now().strftime("%Y:%m:%d %H:%M:%S")

                metadata_overrides = {"DateTimeOriginal": datetime_val}
                result = remove_exif(result)

            filename = Path(self.filepath).name
            output_path = self.output_manager.save(result, filename, metadata_overrides)

            metadata_actions = []
            if exif_opts.get("remove_all"):
                metadata_actions.append("remove_all")
            if exif_opts.get("override"):
                metadata_actions.append("override")

            crop = self.options.get("crop", {})
            record_transform(
                filename=filename,
                crop=crop,
                rotation=self.options.get("rotation", 0),
                brightness=self.options.get("brightness", 0),
                contrast=self.options.get("contrast", 0),
                saturation=self.options.get("saturation", 0),
                noise=self.options.get("noise", 0),
                metadata_actions=metadata_actions,
            )

            self.signals.finished.emit(self.filepath, True, str(output_path), self.options)

        except Exception as e:
            self.signals.finished.emit(self.filepath, False, str(e), {})
