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
from PySide6.QtCore import Qt, Signal, QThreadPool, QRunnable, QObject, QEvent
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QPixmap, QIcon
from PIL import Image
from pathlib import Path
from typing import Optional

from .preview_widget import PreviewWidget
from .options_panel import OptionsPanel
from .log_widget import LogWidget
from .workers import TransformWorker, WorkerSignals
from .workers.batch_worker import BatchTransformWorker
from .widgets import FileListWidget, BusyOverlay
from app.core.preview import PreviewThread, pil_to_qpixmap, create_thumbnail, MAX_PREVIEW_SIZE
from app.core.image_ops import apply_transforms
from app.core.metadata import remove_exif
from app.core.transform_history import record_transform
from app.core.save_output import OutputManager
from app.core.config import load_config, save_config
from app.core.random_transform import (
    RandomTransformConfig,
    generate_random_options,
    format_random_log,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Setakgi - 이미지 세탁기")
        self.setMinimumSize(1200, 800)

        icon_path = Path(__file__).parent.parent / "resources" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Windows 드래그앤 드랍 지원 - MainWindow 레벨
        self.setAcceptDrops(True)

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

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
        self._center_panel.installEventFilter(self)

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

        btn_layout1 = QHBoxLayout()
        self._add_btn = QPushButton("파일 추가")
        self._add_folder_btn = QPushButton("폴더 추가")
        btn_layout1.addWidget(self._add_btn)
        btn_layout1.addWidget(self._add_folder_btn)
        left_layout.addLayout(btn_layout1)

        btn_layout2 = QHBoxLayout()
        self._remove_btn = QPushButton("선택 제거")
        self._clear_btn = QPushButton("전체 제거")
        btn_layout2.addWidget(self._remove_btn)
        btn_layout2.addWidget(self._clear_btn)
        left_layout.addLayout(btn_layout2)

        splitter.addWidget(left_panel)

        self._center_panel = QWidget()
        center_layout = QVBoxLayout(self._center_panel)

        self._preview = PreviewWidget()
        center_layout.addWidget(self._preview)

        self._log_widget = LogWidget()
        center_layout.addWidget(self._log_widget)

        self._overlay = BusyOverlay(self._center_panel)
        self._overlay.setGeometry(self._center_panel.rect())
        self._overlay.hide()
        self._overlay.raise_()

        splitter.addWidget(self._center_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self._options = OptionsPanel()
        right_layout.addWidget(self._options)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        right_layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #ffffff; font-weight: bold;")
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
        self._random_btn = QPushButton("랜덤 변환 실행")
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
        self._add_folder_btn.clicked.connect(self._open_folder_dialog)
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

    def _set_status_message(self, text: str, color: str = "#ffffff"):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _show_completion_feedback(self, label: str):
        success = self._completed
        failed = len(self._failed)
        total = success + failed
        if total == 0:
            return

        color = "#4caf50" if failed == 0 else "#ff9800"
        self._set_status_message(f"{label}: 성공 {success}개 / 실패 {failed}개", color)
        QMessageBox.information(
            self,
            label,
            f"총 {total}개 처리\n성공 {success}개, 실패 {failed}개",
        )

    def _finalize_processing(self, label: str):
        self._overlay.hide_overlay()
        self._progress.setVisible(False)
        self._convert_btn.setEnabled(True)
        self._random_btn.setEnabled(True)
        self._random_mode = False
        self._show_completion_feedback(label)
        self._log_widget.add_separator()
        self._log_widget.add_log(
            f"{label}: 성공 {self._completed}개, 실패 {len(self._failed)}개",
            "info",
        )

    def eventFilter(self, obj, event):
        if obj == self._center_panel and event.type() == QEvent.Resize:
            self._overlay.setGeometry(self._center_panel.rect())
        return super().eventFilter(obj, event)

    def _add_files(self, files: list[str]):
        # 기존 파일 모두 제거
        self._file_list.clear()
        self._files.clear()
        self._current_file = None
        self._current_image = None

        # 새 파일만 추가
        for f in files:
            if f not in self._files:
                self._files.append(f)
                item = QListWidgetItem(Path(f).name)
                item.setData(Qt.ItemDataRole.UserRole, f)
                self._file_list.addItem(item)

        if self._files:
            self._file_list.setCurrentRow(0)

        # 새로 추가된 파일의 디렉토리를 출력 폴더로 자동 설정
        if files:
            output_dir = str(Path(files[0]).parent)
            self._config["last_output_dir"] = output_dir
            save_config(self._config)
            self._output_path_label.setText(f"출력 폴더: {output_dir}")

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

    def _open_folder_dialog(self):
        """폴더 선택 → 내부 이미지 파일 자동 추가"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "이미지 폴더 선택",
            self._config.get("last_input_dir", ""),
        )
        if folder:
            self._config["last_input_dir"] = folder
            save_config(self._config)

            # 폴더 내 이미지 파일 검색
            image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
            folder_path = Path(folder)
            files = [
                str(f) for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            if files:
                files.sort()  # 파일명 순 정렬
                self._add_files(files)
            else:
                QMessageBox.information(self, "알림", "폴더에 이미지 파일이 없습니다.")

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
        self._perspective_corners = None
        self._preview.reset_corner_offsets()
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
            self._preview.reset_corner_offsets()

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
            self._preview.reset_corner_offsets()
        else:
            # 프리뷰 위젯의 set_uniform_offset 사용
            # perspective_changed 시그널이 발생하여 _on_perspective_changed에서 처리됨
            self._preview.set_uniform_offset(offset)

    def _on_reset_requested(self):
        self._perspective_corners = None
        self._preview.reset_corner_offsets()
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
        self._random_btn.setEnabled(False)
        self._set_status_message("변환 중...", "#90caf9")
        self._overlay.show_message("변환 중")

        self._completed = 0
        self._failed = []

        options = self._options.get_options()
        output_manager = OutputManager(output_dir, options)

        if self._perspective_corners:
            options["perspective_corners"] = self._perspective_corners
            # 썸네일 크기 저장 (원근 변형 스케일링용)
            if self._current_image:
                thumb = create_thumbnail(self._current_image, MAX_PREVIEW_SIZE)
                options["thumb_w"] = thumb.size[0]
                options["thumb_h"] = thumb.size[1]

        # 병렬 배치 처리 (멀티프로세스)
        self._batch_worker = BatchTransformWorker(
            self._files,
            options,
            output_manager.get_output_dir(),
            options.get("output_format", "jpeg"),
        )
        self._batch_worker.signals.finished.connect(
            self._on_worker_finished, Qt.ConnectionType.QueuedConnection
        )
        self._batch_worker.signals.all_done.connect(
            self._on_batch_done, Qt.ConnectionType.QueuedConnection
        )
        self._batch_worker.start()

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
        if self._random_mode and total_done >= len(self._files):
            self._on_random_done()

    def _on_batch_done(self):
        """배치 처리 완료"""
        self._finalize_processing("변환 완료")

    def _on_random_done(self):
        """랜덤 변환 완료"""
        self._finalize_processing("랜덤 변환 완료")

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
        self._log_widget.add_log("랜덤 변환 시작", "info")
        self._log_widget.add_separator()

        self._progress.setVisible(True)
        self._progress.setMaximum(len(self._files))
        self._progress.setValue(0)
        self._convert_btn.setEnabled(False)
        self._random_btn.setEnabled(False)
        self._set_status_message("랜덤 변형 중...", "#90caf9")
        self._overlay.show_message("랜덤 변형 중")

        self._completed = 0
        self._failed = []
        self._workers = []

        # 랜덤 모드용 폴더명 + UI에서 선택한 출력 포맷
        ui_options = self._options.get_options()
        random_folder_options = {
            "random": True,
            "output_format": ui_options.get("output_format", "jpeg"),
        }
        output_manager = OutputManager(output_dir, random_folder_options)

        # UI에서 랜덤 설정값 가져오기
        random_cfg = self._options.get_random_config()
        random_config = RandomTransformConfig(
            crop_range=random_cfg.get("crop_range", 6.0),
            rotation_range=random_cfg.get("rotation_range", 3.0),
            noise_range=random_cfg.get("noise_range", 4.0),
            perspective_range=random_cfg.get("perspective_range", 1.6),
            date_days_back=random_cfg.get("date_days_back", 7),
        )

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
                    random_config, thumb_w, thumb_h,
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
        total_done = self._completed + len(self._failed)
        if total_done >= len(self._files):
            self._on_random_done()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Windows 드래그앤 드랍 - MainWindow 레벨 지원"""
        if event.mimeData().hasUrls():
            self._file_list.setStyleSheet(self._file_list.STYLE_DRAG_OVER)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._file_list.setStyleSheet(self._file_list.STYLE_NORMAL)
        event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트 처리 - 파일/폴더 모두 지원"""
        self._file_list.setStyleSheet(self._file_list.STYLE_NORMAL)
        files = []
        image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue

            p = Path(path)
            # 폴더인 경우 내부 이미지 파일 추가
            if p.is_dir():
                for f in p.iterdir():
                    if f.is_file() and f.suffix.lower() in image_extensions:
                        files.append(str(f))
            # 이미지 파일인 경우
            elif p.suffix.lower() in image_extensions:
                files.append(path)

        if files:
            files.sort()
            self._add_files(files)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def closeEvent(self, event):
        save_config(self._config)
        self._thread_pool.waitForDone()
        super().closeEvent(event)
