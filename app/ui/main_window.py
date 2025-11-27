from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QLabel,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QThreadPool, QRunnable, QObject
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PIL import Image
from pathlib import Path
from typing import Optional

from .preview_widget import PreviewWidget
from .options_panel import OptionsPanel
from .log_widget import LogWidget
from app.core.preview import PreviewThread, pil_to_qpixmap, create_thumbnail, MAX_PREVIEW_SIZE
from app.core.image_ops import apply_transforms
from app.core.metadata import (
    read_exif,
    remove_exif,
    create_exif_bytes,
    apply_exif_overrides,
)
from app.core.transform_history import record_transform
from app.core.save_output import OutputManager
from app.core.config import load_config, save_config
from app.core.random_transform import (
    RandomTransformConfig,
    generate_random_options,
    format_random_log,
)


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

            perspective_corners = None
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

            exif_opts = self.options.get("exif", {})
            exif_bytes = None

            if exif_opts.get("remove_all"):
                result = remove_exif(result)
            elif exif_opts.get("override"):
                override_data = {
                    "Make": exif_opts.get("make", ""),
                    "Model": exif_opts.get("model", ""),
                    "DateTimeOriginal": exif_opts.get("datetime", ""),
                }
                override_data = {k: v for k, v in override_data.items() if v}
                if override_data:
                    exif_bytes = create_exif_bytes(override_data)
                result = remove_exif(result)

            filename = Path(self.filepath).name
            output_path = self.output_manager.save(result, filename, exif_bytes)

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


class FileListWidget(QListWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
                files.append(path)

        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Setakgi - 이미지 세탁기")
        self.setMinimumSize(1200, 800)

        self._files: list[str] = []
        self._current_file: Optional[str] = None
        self._current_image: Optional[Image.Image] = None
        self._thread_pool = QThreadPool()
        self._preview_thread: Optional[PreviewThread] = None

        self._config = load_config()
        self._perspective_corners: Optional[list] = None
        self._loading_new_image = False
        self._completed = 0
        self._failed: list = []
        self._output_manager: Optional[OutputManager] = None
        self._workers: list = []
        self._random_mode = False
        self._random_config = RandomTransformConfig()

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        # 자유변형 모드 초기화 (신호 연결 후 활성화)
        self._preview.set_free_transform_mode(True)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        file_label = QLabel("파일 목록")
        file_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(file_label)

        self._file_list = FileListWidget()
        left_layout.addWidget(self._file_list)

        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("파일 추가")
        self._remove_btn = QPushButton("선택 제거")
        self._clear_btn = QPushButton("전체 제거")
        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        btn_layout.addWidget(self._clear_btn)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        self._preview = PreviewWidget()
        center_layout.addWidget(self._preview)

        self._log_widget = LogWidget()
        center_layout.addWidget(self._log_widget)

        splitter.addWidget(center_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self._options = OptionsPanel()
        right_layout.addWidget(self._options)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        right_layout.addWidget(self._progress)

        self._status_label = QLabel("")
        right_layout.addWidget(self._status_label)

        action_layout = QHBoxLayout()
        self._output_btn = QPushButton("출력 폴더 선택")
        self._convert_btn = QPushButton("변환 실행")
        self._convert_btn.setStyleSheet(
            "background-color: #4285f4; color: white; font-weight: bold; padding: 10px;"
        )
        action_layout.addWidget(self._output_btn)
        action_layout.addWidget(self._convert_btn)
        right_layout.addLayout(action_layout)

        random_layout = QHBoxLayout()
        self._random_btn = QPushButton("🎲 랜덤 변환 실행")
        self._random_btn.setStyleSheet(
            "background-color: #9c27b0; color: white; font-weight: bold; padding: 10px;"
        )
        random_layout.addWidget(self._random_btn)
        right_layout.addLayout(random_layout)

        self._output_path_label = QLabel("출력 폴더: 미선택")
        right_layout.addWidget(self._output_path_label)

        splitter.addWidget(right_panel)

        splitter.setSizes([180, 520, 400])

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        self._file_list.files_dropped.connect(self._add_files)
        self._file_list.currentRowChanged.connect(self._on_file_selected)

        self._add_btn.clicked.connect(self._open_file_dialog)
        self._remove_btn.clicked.connect(self._remove_selected)
        self._clear_btn.clicked.connect(self._clear_files)

        self._options.options_changed.connect(self._on_options_changed)
        self._options.free_transform_toggled.connect(self._on_free_transform_toggle)
        self._options.reset_requested.connect(self._on_reset_requested)
        self._options.perspective_offset_changed.connect(self._on_perspective_offset_changed)
        self._preview.perspective_changed.connect(self._on_perspective_changed)

        self._output_btn.clicked.connect(self._select_output_folder)
        self._convert_btn.clicked.connect(self._start_conversion)
        self._random_btn.clicked.connect(self._start_random_conversion)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QListWidget {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #4285f4;
            }
            QPushButton {
                background-color: #555;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #555;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                background: #4285f4;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4285f4;
            }
            """
        )

    def _add_files(self, files: list[str]):
        for f in files:
            if f not in self._files:
                self._files.append(f)
                item = QListWidgetItem(Path(f).name)
                item.setData(Qt.ItemDataRole.UserRole, f)
                self._file_list.addItem(item)

        if self._files and self._current_file is None:
            self._file_list.setCurrentRow(0)

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "이미지 파일 선택",
            self._config.get("last_input_dir", ""),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if files:
            self._config["last_input_dir"] = str(Path(files[0]).parent)
            save_config(self._config)
            self._add_files(files)

    def _remove_selected(self):
        row = self._file_list.currentRow()
        if row >= 0:
            self._file_list.takeItem(row)
            del self._files[row]
            if not self._files:
                self._current_file = None
                self._current_image = None
                self._preview.set_image(QPixmap())

    def _clear_files(self):
        self._file_list.clear()
        self._files.clear()
        self._current_file = None
        self._current_image = None
        self._preview.set_image(QPixmap())

    def _on_file_selected(self, row: int):
        if row < 0 or row >= len(self._files):
            return

        self._current_file = self._files[row]
        self._load_image(self._current_file)

    def _load_image(self, filepath: str):
        try:
            self._loading_new_image = True
            self._current_image = Image.open(filepath)
            w, h = self._current_image.size

            self._options.set_original_size(w, h)
            self._preview.set_keep_ratio(True)
            self._perspective_corners = None

            self._update_preview()

        except Exception as e:
            self._loading_new_image = False
            QMessageBox.warning(self, "오류", f"이미지 로드 실패: {e}")

    def _update_preview(self):
        if self._current_image is None:
            return

        if self._preview_thread and self._preview_thread.isRunning():
            self._preview_thread.quit()
            self._preview_thread.wait()

        self._preview_thread = PreviewThread(self)
        self._preview_thread.set_source(self._current_image)

        options = self._options.get_options()
        if self._perspective_corners:
            options["perspective_corners"] = self._perspective_corners

        self._preview_thread.set_options(options)
        self._preview_thread.preview_ready.connect(self._on_preview_ready)
        self._preview_thread.preview_error.connect(self._on_preview_error)
        self._preview_thread.start()

    def _on_preview_ready(self, pixmap: QPixmap):
        reset = self._loading_new_image or self._perspective_corners is None
        self._loading_new_image = False
        self._preview.set_image(pixmap, reset_transform=reset)
        opts = self._options.get_options()
        self._preview.update_info(opts.get("width", 0), opts.get("height", 0))

        if self._current_image:
            rotation = opts.get("rotation", 0)
            crop = opts.get("crop", {})
            crop_amount = crop.get("top", 0)

            orig_w, orig_h = self._current_image.size
            max_size = 512
            ratio = min(max_size / orig_w, max_size / orig_h, 1.0)
            thumb_w = int(orig_w * ratio)
            thumb_h = int(orig_h * ratio)

            if crop_amount < 0:
                pre_rot_w = thumb_w + abs(crop_amount) * 2
                pre_rot_h = thumb_h + abs(crop_amount) * 2
            else:
                pre_rot_w = max(2, thumb_w - crop_amount * 2)
                pre_rot_h = max(2, thumb_h - crop_amount * 2)

            self._preview.set_rotation(rotation, (pre_rot_w, pre_rot_h))

    def _on_preview_error(self, error: str):
        self._status_label.setText(f"미리보기 오류: {error}")

    def _on_options_changed(self, options: dict):
        self._update_preview()

    def _on_free_transform_toggle(self, enabled: bool):
        self._preview.set_free_transform_mode(enabled)
        if not enabled:
            self._perspective_corners = None
        self._update_preview()

    def _on_perspective_changed(self, corners: list):
        self._perspective_corners = corners
        self._update_preview()

    def _on_perspective_offset_changed(self, offset: float):
        """수동 perspective offset 변경 시 호출"""
        if self._current_image is None:
            return

        if offset == 0:
            self._perspective_corners = None
        else:
            # 현재 이미지의 thumbnail 크기 기준으로 코너 계산
            orig_w, orig_h = self._current_image.size
            ratio = min(MAX_PREVIEW_SIZE / orig_w, MAX_PREVIEW_SIZE / orig_h, 1.0)
            thumb_w = int(orig_w * ratio)
            thumb_h = int(orig_h * ratio)

            # 각 코너에 offset 적용
            self._perspective_corners = [
                (0 + offset, 0 + offset),           # top-left
                (thumb_w - offset, 0 + offset),    # top-right
                (thumb_w - offset, thumb_h - offset),  # bottom-right
                (0 + offset, thumb_h - offset),    # bottom-left
            ]

        self._update_preview()

    def _on_reset_requested(self):
        self._perspective_corners = None
        if self._current_image:
            self._loading_new_image = True
            self._update_preview()

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "출력 폴더 선택",
            self._config.get("last_output_dir", ""),
        )
        if folder:
            self._config["last_output_dir"] = folder
            save_config(self._config)
            self._output_path_label.setText(f"출력 폴더: {folder}")

    def _start_conversion(self):
        if not self._files:
            QMessageBox.warning(self, "경고", "변환할 파일이 없습니다.")
            return

        output_dir = self._config.get("last_output_dir", "")
        if not output_dir:
            QMessageBox.warning(self, "경고", "출력 폴더를 선택하세요.")
            return

        self._progress.setVisible(True)
        self._progress.setMaximum(len(self._files))
        self._progress.setValue(0)
        self._convert_btn.setEnabled(False)

        self._completed = 0
        self._failed = []
        self._workers = []

        options = self._options.get_options()
        output_manager = OutputManager(output_dir, options)

        if self._perspective_corners:
            options["perspective_corners"] = self._perspective_corners

        for filepath in self._files:
            worker = TransformWorker(filepath, options, output_manager)
            worker.setAutoDelete(False)
            worker.signals.finished.connect(
                self._on_worker_finished, Qt.ConnectionType.QueuedConnection
            )
            self._workers.append(worker)
            self._thread_pool.start(worker)

        self._output_manager = output_manager

    def _on_worker_finished(self, filepath: str, success: bool, result: str, applied_options: dict):
        filename = Path(filepath).name
        if success:
            self._completed += 1
            if self._random_mode and applied_options:
                log_msg = format_random_log(filename, applied_options)
                self._log_widget.add_log(log_msg, "success")
        else:
            self._failed.append((filepath, result))
            self._log_widget.add_log(f"[{filename}] 오류: {result}", "error")

        total_done = self._completed + len(self._failed)
        self._progress.setValue(total_done)

        if total_done >= len(self._files):
            self._progress.setVisible(False)
            self._convert_btn.setEnabled(True)
            self._random_btn.setEnabled(True)
            self._workers.clear()
            self._random_mode = False

            self._status_label.setText("변환 완료")
            self._log_widget.add_separator()
            self._log_widget.add_log(
                f"변환 완료: 성공 {self._completed}개, 실패 {len(self._failed)}개", "info"
            )
            QMessageBox.information(
                self,
                "완료",
                f"변환이 완료되었습니다.\n출력 폴더: {self._output_manager.get_output_dir()}",
            )

    def _start_random_conversion(self):
        """랜덤 변형 실행 - 각 이미지에 다른 랜덤 값 적용"""
        if not self._files:
            QMessageBox.warning(self, "경고", "변환할 파일이 없습니다.")
            return

        output_dir = self._config.get("last_output_dir", "")
        if not output_dir:
            QMessageBox.warning(self, "경고", "출력 폴더를 선택하세요.")
            return

        self._random_mode = True
        self._log_widget.clear()
        self._log_widget.add_log("🎲 랜덤 변환 시작", "info")
        self._log_widget.add_separator()

        self._progress.setVisible(True)
        self._progress.setMaximum(len(self._files))
        self._progress.setValue(0)
        self._convert_btn.setEnabled(False)
        self._random_btn.setEnabled(False)

        self._completed = 0
        self._failed = []
        self._workers = []

        # 랜덤 모드용 폴더명
        random_folder_options = {"random": True}
        output_manager = OutputManager(output_dir, random_folder_options)

        for filepath in self._files:
            try:
                img = Image.open(filepath)
                orig_w, orig_h = img.size
                img.close()

                # thumbnail 크기 계산 (MAX_PREVIEW_SIZE 기준)
                ratio = min(MAX_PREVIEW_SIZE / orig_w, MAX_PREVIEW_SIZE / orig_h, 1.0)
                thumb_w = int(orig_w * ratio)
                thumb_h = int(orig_h * ratio)

                # 각 이미지별로 새로운 랜덤 옵션 생성 (thumbnail 좌표 기준)
                random_options = generate_random_options(
                    self._random_config, thumb_w, thumb_h,
                    include_perspective=True,
                    include_date=True,
                )

                worker = TransformWorker(filepath, random_options, output_manager)
                worker.setAutoDelete(False)
                worker.signals.finished.connect(
                    self._on_worker_finished, Qt.ConnectionType.QueuedConnection
                )
                self._workers.append(worker)
                self._thread_pool.start(worker)

            except Exception as e:
                self._log_widget.add_log(f"[{Path(filepath).name}] 파일 열기 실패: {e}", "error")
                self._failed.append((filepath, str(e)))

        self._output_manager = output_manager

    def closeEvent(self, event):
        save_config(self._config)
        self._thread_pool.waitForDone()
        super().closeEvent(event)
