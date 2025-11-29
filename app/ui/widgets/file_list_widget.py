from pathlib import Path

from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent


class FileListWidget(QListWidget):
    files_dropped = Signal(list)

    STYLE_NORMAL = """
        QListWidget {
            background-color: #3d3d3d;
            border: 2px solid #555;
            border-radius: 4px;
        }
    """
    STYLE_DRAG_OVER = """
        QListWidget {
            background-color: #3d4d5d;
            border: 2px dashed #4285f4;
            border-radius: 4px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setStyleSheet(self.STYLE_NORMAL)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setStyleSheet(self.STYLE_DRAG_OVER)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setStyleSheet(self.STYLE_NORMAL)
        event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self.STYLE_NORMAL)
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
            self.files_dropped.emit(files)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()
