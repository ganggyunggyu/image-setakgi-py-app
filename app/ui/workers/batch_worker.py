"""병렬 배치 처리 워커

ProcessPoolExecutor를 사용해 이미지 처리를 병렬화
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

from PySide6.QtCore import QObject, QThread, Signal
from PIL import Image, ImageOps

from app.core.image_ops import apply_transforms
from app.core.metadata import remove_exif
from app.core.save_output import save_transformed_image


def _init_worker():
    """멀티프로세스 워커 초기화: OpenCV 내부 스레드 제한"""
    try:
        import cv2

        cv2.setNumThreads(1)
    except Exception:
        return


def _process_single_image(args: dict) -> dict:
    """단일 이미지 처리 (멀티프로세스용 - 모듈 레벨 함수)"""
    filepath = args["filepath"]
    options = args["options"]
    output_dir = Path(args["output_dir"])
    output_format = args.get("output_format", "jpeg")

    try:
        img = Image.open(filepath)
        img = ImageOps.exif_transpose(img) if img else img

        # 원근 변형 좌표 스케일링
        perspective_corners = None
        if options.get("perspective_corners"):
            orig_w, orig_h = img.size
            thumb_w = options.get("thumb_w", orig_w)
            thumb_h = options.get("thumb_h", orig_h)
            scale_x = orig_w / thumb_w
            scale_y = orig_h / thumb_h
            perspective_corners = [
                (x * scale_x, y * scale_y)
                for x, y in options["perspective_corners"]
            ]

        result = apply_transforms(
            img,
            rotation=options.get("rotation", 0),
            brightness=options.get("brightness", 0),
            contrast=options.get("contrast", 0),
            saturation=options.get("saturation", 0),
            noise=options.get("noise", 0),
            perspective_corners=perspective_corners,
            crop=options.get("crop"),
        )

        # EXIF 처리
        exif_opts = options.get("exif", {})
        metadata_overrides = None

        if exif_opts.get("remove_all"):
            result = remove_exif(result)
        elif exif_opts.get("override"):
            from datetime import datetime as dt
            datetime_val = exif_opts.get("datetime", "")
            if not datetime_val:
                datetime_val = dt.now().strftime("%Y:%m:%d %H:%M:%S")
            metadata_overrides = {"DateTimeOriginal": datetime_val}
            result = remove_exif(result)

        filename = Path(filepath).name
        output_path = save_transformed_image(
            result, output_dir, filename, metadata_overrides, output_format
        )

        return {
            "filepath": filepath,
            "success": True,
            "result": str(output_path),
            "options": options,
        }

    except Exception as e:
        return {
            "filepath": filepath,
            "success": False,
            "result": str(e),
            "options": {},
        }


class BatchWorkerSignals(QObject):
    """배치 워커 시그널"""
    progress = Signal(int, int)  # current, total
    finished = Signal(str, bool, str, dict)  # filepath, success, result, options
    all_done = Signal()


class BatchTransformWorker(QThread):
    """병렬 배치 처리 워커

    사용법:
        worker = BatchTransformWorker(files, options, output_dir, output_format)
        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        worker.signals.all_done.connect(on_all_done)
        worker.start()
    """

    def __init__(
        self,
        files: list[str],
        options: dict,
        output_dir: str,
        output_format: str = "jpeg",
        max_workers: int = None,
    ):
        super().__init__()
        self.files = files
        self.options = options
        self.output_dir = output_dir
        self.output_format = output_format
        self.max_workers = max_workers or max(1, mp.cpu_count() - 1)
        self.signals = BatchWorkerSignals()
        self._cancelled = False

    def cancel(self):
        """처리 취소"""
        self._cancelled = True

    def run(self):
        """병렬 처리 실행"""
        try:
            # 작업 목록 생성
            tasks = [
                {
                    "filepath": f,
                    "options": self.options,
                    "output_dir": self.output_dir,
                    "output_format": self.output_format,
                }
                for f in self.files
            ]

            total = len(tasks)
            completed = 0

            with ProcessPoolExecutor(
                max_workers=self.max_workers,
                initializer=_init_worker,
            ) as executor:
                futures = {executor.submit(_process_single_image, t): t for t in tasks}

                for future in as_completed(futures):
                    if self._cancelled:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    try:
                        result = future.result()
                    except Exception as e:
                        # 개별 작업 실패 처리
                        task = futures[future]
                        result = {
                            "filepath": task["filepath"],
                            "success": False,
                            "result": str(e),
                            "options": {},
                        }

                    completed += 1
                    self.signals.progress.emit(completed, total)
                    self.signals.finished.emit(
                        result["filepath"],
                        result["success"],
                        result["result"],
                        result["options"],
                    )
        finally:
            # 항상 완료 시그널 발생
            self.signals.all_done.emit()
