from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsPathItem,
    QWidget,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QCursor, QPainter, QPainterPath

HANDLE_SIZE = 10


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, position: str, parent=None):
        super().__init__(parent)
        self.position = position
        self.setRect(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE)
        self.setBrush(QBrush(QColor(66, 133, 244)))
        self.setPen(QPen(QColor(255, 255, 255), 1))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        self.setCursor(self._get_cursor())

    def _get_cursor(self) -> QCursor:
        cursors = {
            "top_left": Qt.CursorShape.SizeFDiagCursor,
            "top_right": Qt.CursorShape.SizeBDiagCursor,
            "bottom_left": Qt.CursorShape.SizeBDiagCursor,
            "bottom_right": Qt.CursorShape.SizeFDiagCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
        }
        return QCursor(cursors.get(self.position, Qt.CursorShape.ArrowCursor))


class TransformableImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, False)


class PreviewGraphicsView(QGraphicsView):
    size_changed = Signal(int, int)
    transform_started = Signal()
    transform_ended = Signal()
    perspective_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: #2d2d2d; border: 1px solid #555;")

        self._image_item: TransformableImageItem = None
        self._handles: dict[str, ResizeHandle] = {}
        self._border_rect: QGraphicsRectItem = None

        self._dragging = False
        self._drag_handle: str = None
        self._drag_start_pos: QPointF = None
        self._original_rect: QRectF = None

        self._keep_ratio = True
        self._original_aspect = 1.0

        self._current_width = 0
        self._current_height = 0

        self._free_transform_mode = False
        self._corner_positions: dict[str, QPointF] = {}

    def set_keep_ratio(self, keep: bool):
        self._keep_ratio = keep

    def set_free_transform_mode(self, enabled: bool):
        self._free_transform_mode = enabled
        if self._image_item:
            self._create_handles()
            self._update_handles_position()
            if enabled:
                rect = self._image_item.boundingRect()
                self._corner_positions = {
                    "top_left": QPointF(rect.left(), rect.top()),
                    "top_right": QPointF(rect.right(), rect.top()),
                    "bottom_right": QPointF(rect.right(), rect.bottom()),
                    "bottom_left": QPointF(rect.left(), rect.bottom()),
                }

    def set_image(self, pixmap: QPixmap):
        self._scene.clear()
        self._handles.clear()
        self._corner_positions.clear()

        if pixmap.isNull():
            return

        self._image_item = TransformableImageItem(pixmap)
        self._scene.addItem(self._image_item)

        self._current_width = pixmap.width()
        self._current_height = pixmap.height()
        self._original_aspect = pixmap.width() / pixmap.height() if pixmap.height() > 0 else 1

        if self._free_transform_mode:
            rect = self._image_item.boundingRect()
            self._corner_positions = {
                "top_left": QPointF(rect.left(), rect.top()),
                "top_right": QPointF(rect.right(), rect.top()),
                "bottom_right": QPointF(rect.right(), rect.bottom()),
                "bottom_left": QPointF(rect.left(), rect.bottom()),
            }

        self._create_border()
        self._create_handles()
        self._update_handles_position()

        self.fitInView(self._image_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._scene.setSceneRect(self._scene.itemsBoundingRect())

    def _create_border(self):
        if self._image_item is None:
            return

        rect = self._image_item.boundingRect()
        self._border_rect = QGraphicsRectItem(rect)
        self._border_rect.setPen(QPen(QColor(66, 133, 244), 2, Qt.PenStyle.DashLine))
        self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
        self._scene.addItem(self._border_rect)

    def _create_handles(self):
        for handle in self._handles.values():
            self._scene.removeItem(handle)
        self._handles.clear()

        # 자유변형 모드에서만 핸들 표시
        if self._free_transform_mode:
            positions = ["top_left", "top_right", "bottom_right", "bottom_left"]

            for pos in positions:
                handle = ResizeHandle(pos)
                self._scene.addItem(handle)
                self._handles[pos] = handle

    def _update_handles_position(self):
        if self._image_item is None or not self._handles:
            return

        if self._free_transform_mode and self._corner_positions:
            for name, pos in self._corner_positions.items():
                if name in self._handles:
                    self._handles[name].setPos(pos)

            if self._border_rect and len(self._corner_positions) == 4:
                path = QPainterPath()
                corners = [
                    self._corner_positions["top_left"],
                    self._corner_positions["top_right"],
                    self._corner_positions["bottom_right"],
                    self._corner_positions["bottom_left"]
                ]
                path.moveTo(corners[0])
                for corner in corners[1:]:
                    path.lineTo(corner)
                path.closeSubpath()
                self._scene.removeItem(self._border_rect)
                self._border_rect = QGraphicsPathItem(path)
                self._border_rect.setPen(QPen(QColor(66, 133, 244), 2, Qt.PenStyle.DashLine))
                self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
                self._scene.addItem(self._border_rect)
        else:
            rect = self._image_item.boundingRect()
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

            positions = {
                "top_left": (x, y),
                "top": (x + w / 2, y),
                "top_right": (x + w, y),
                "left": (x, y + h / 2),
                "right": (x + w, y + h / 2),
                "bottom_left": (x, y + h),
                "bottom": (x + w / 2, y + h),
                "bottom_right": (x + w, y + h),
            }

            for name, (px, py) in positions.items():
                if name in self._handles:
                    self._handles[name].setPos(px, py)

            if self._border_rect:
                if not isinstance(self._border_rect, QGraphicsRectItem):
                    self._scene.removeItem(self._border_rect)
                    self._border_rect = QGraphicsRectItem(rect)
                    self._border_rect.setPen(QPen(QColor(66, 133, 244), 2, Qt.PenStyle.DashLine))
                    self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
                    self._scene.addItem(self._border_rect)
                else:
                    self._border_rect.setRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            for name, handle in self._handles.items():
                if handle.contains(handle.mapFromScene(scene_pos)):
                    self._dragging = True
                    self._drag_handle = name
                    self._drag_start_pos = scene_pos
                    self._original_rect = self._image_item.boundingRect() if self._image_item else QRectF()
                    self.transform_started.emit()
                    event.accept()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._image_item:
            scene_pos = self.mapToScene(event.pos())

            if self._free_transform_mode:
                if self._drag_handle in self._corner_positions:
                    self._corner_positions[self._drag_handle] = scene_pos
                    self._update_handles_position()

                    image_corners = [
                        self._image_item.mapFromScene(self._corner_positions["top_left"]),
                        self._image_item.mapFromScene(self._corner_positions["top_right"]),
                        self._image_item.mapFromScene(self._corner_positions["bottom_right"]),
                        self._image_item.mapFromScene(self._corner_positions["bottom_left"])
                    ]
                    corner_list = [(c.x(), c.y()) for c in image_corners]
                    self.perspective_changed.emit(corner_list)

                event.accept()
                return

            delta = scene_pos - self._drag_start_pos

            new_width = self._current_width
            new_height = self._current_height

            if "right" in self._drag_handle:
                new_width = max(10, int(self._current_width + delta.x()))
            elif "left" in self._drag_handle:
                new_width = max(10, int(self._current_width - delta.x()))

            if "bottom" in self._drag_handle:
                new_height = max(10, int(self._current_height + delta.y()))
            elif "top" in self._drag_handle:
                new_height = max(10, int(self._current_height - delta.y()))

            if self._keep_ratio:
                if "left" in self._drag_handle or "right" in self._drag_handle:
                    if "top" not in self._drag_handle and "bottom" not in self._drag_handle:
                        new_height = int(new_width / self._original_aspect)
                elif "top" in self._drag_handle or "bottom" in self._drag_handle:
                    new_width = int(new_height * self._original_aspect)

                if self._drag_handle in ["top_left", "top_right", "bottom_left", "bottom_right"]:
                    if abs(delta.x()) > abs(delta.y()):
                        new_height = int(new_width / self._original_aspect)
                    else:
                        new_width = int(new_height * self._original_aspect)

            self.size_changed.emit(new_width, new_height)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._drag_handle = None
            self.transform_ended.emit()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def get_current_size(self) -> tuple[int, int]:
        return self._current_width, self._current_height

    def update_display_size(self, width: int, height: int):
        self._current_width = width
        self._current_height = height


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

    def set_image(self, pixmap: QPixmap):
        self._view.set_image(pixmap)
        if not pixmap.isNull():
            self._info_label.setText(f"크기: {pixmap.width()} x {pixmap.height()}")
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
        self._info_label.setText(f"크기: {width} x {height}")
        self._view.update_display_size(width, height)
