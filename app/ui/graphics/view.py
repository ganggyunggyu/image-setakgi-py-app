"""프리뷰 그래픽스 뷰"""
import math
from typing import Optional

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPathItem
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter, QPainterPath

from .handles import ResizeHandle
from .items import TransformableImageItem

# 상수 정의
BORDER_WIDTH = 2
PADDING_RATIO = 0.05
MIN_SIZE = 10


class PreviewGraphicsView(QGraphicsView):
    """이미지 프리뷰 및 변형을 위한 그래픽스 뷰"""

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

        self._image_item: Optional[TransformableImageItem] = None
        self._handles: dict[str, ResizeHandle] = {}
        self._border_rect: Optional[QGraphicsRectItem | QGraphicsPathItem] = None

        self._dragging = False
        self._drag_handle: Optional[str] = None
        self._drag_start_pos: Optional[QPointF] = None
        self._original_rect: Optional[QRectF] = None

        self._keep_ratio = True
        self._original_aspect = 1.0

        self._current_width = 0
        self._current_height = 0

        self._free_transform_mode = False
        self._corner_positions: dict[str, QPointF] = {}

        self._rotation_angle = 0.0
        self._original_size: tuple[int, int] = (0, 0)

    def set_keep_ratio(self, keep: bool) -> None:
        """비율 유지 여부 설정"""
        self._keep_ratio = keep

    def set_free_transform_mode(self, enabled: bool) -> None:
        """자유 변형 모드 설정"""
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

    def set_image(self, pixmap: QPixmap, reset_transform: bool = False) -> None:
        """이미지 설정"""
        saved_corners = self._corner_positions.copy() if not reset_transform and self._free_transform_mode else {}

        self._scene.clear()
        self._handles.clear()
        self._border_rect = None
        self._rotation_angle = 0.0
        self._original_size = (0, 0)

        if pixmap.isNull():
            self._corner_positions.clear()
            return

        self._image_item = TransformableImageItem(pixmap)
        self._scene.addItem(self._image_item)

        self._current_width = pixmap.width()
        self._current_height = pixmap.height()
        self._original_aspect = pixmap.width() / pixmap.height() if pixmap.height() > 0 else 1

        if self._free_transform_mode:
            rect = self._image_item.boundingRect()
            if saved_corners:
                self._corner_positions = saved_corners
            else:
                self._corner_positions = {
                    "top_left": QPointF(rect.left(), rect.top()),
                    "top_right": QPointF(rect.right(), rect.top()),
                    "bottom_right": QPointF(rect.right(), rect.bottom()),
                    "bottom_left": QPointF(rect.left(), rect.bottom()),
                }

        self._create_border()
        self._create_handles()
        self._update_handles_position()

        rect = self._scene.itemsBoundingRect()
        padding_x = rect.width() * PADDING_RATIO
        padding_y = rect.height() * PADDING_RATIO
        padded_rect = rect.adjusted(-padding_x, -padding_y, padding_x, padding_y)
        self._scene.setSceneRect(padded_rect)
        self.fitInView(padded_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _create_border(self) -> None:
        """테두리 생성"""
        if self._image_item is None:
            return

        rect = self._image_item.boundingRect()
        self._border_rect = QGraphicsRectItem(rect)
        self._border_rect.setPen(QPen(QColor(66, 133, 244), BORDER_WIDTH, Qt.PenStyle.DashLine))
        self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
        self._scene.addItem(self._border_rect)

    def _create_handles(self) -> None:
        """핸들 생성"""
        for handle in self._handles.values():
            self._scene.removeItem(handle)
        self._handles.clear()

        if self._free_transform_mode:
            positions = ["top_left", "top_right", "bottom_right", "bottom_left"]

            for pos in positions:
                handle = ResizeHandle(pos)
                self._scene.addItem(handle)
                self._handles[pos] = handle

    def _update_handles_position(self) -> None:
        """핸들 위치 업데이트"""
        if self._image_item is None:
            return

        if self._free_transform_mode and self._corner_positions:
            self._update_free_transform_handles()
        elif self._handles:
            self._update_resize_handles()
        else:
            self._update_border_only()

    def _update_free_transform_handles(self) -> None:
        """자유 변형 모드 핸들 위치 업데이트"""
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
            self._border_rect.setPen(QPen(QColor(66, 133, 244), BORDER_WIDTH, Qt.PenStyle.DashLine))
            self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
            self._scene.addItem(self._border_rect)

    def _update_resize_handles(self) -> None:
        """리사이즈 모드 핸들 위치 업데이트"""
        if self._image_item is None:
            return

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

        self._update_border_rect(rect)

    def _update_border_only(self) -> None:
        """테두리만 업데이트 (핸들 없는 경우)"""
        if self._image_item is None:
            return

        if self._rotation_angle != 0 and self._original_size[0] > 0:
            self._update_rotated_border()
        else:
            rect = self._image_item.boundingRect()
            self._update_border_rect(rect)

    def _update_rotated_border(self) -> None:
        """회전된 테두리 업데이트"""
        if self._image_item is None:
            return

        orig_w, orig_h = self._original_size
        if orig_w <= 0 or orig_h <= 0:
            return

        rect = self._image_item.boundingRect()
        cx = rect.center().x()
        cy = rect.center().y()

        half_w = orig_w / 2
        half_h = orig_h / 2

        rad = math.radians(self._rotation_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        corners = [
            (-half_w, -half_h),
            (half_w, -half_h),
            (half_w, half_h),
            (-half_w, half_h),
        ]

        rotated_corners = []
        for x, y in corners:
            rx = x * cos_a - y * sin_a + cx
            ry = x * sin_a + y * cos_a + cy
            rotated_corners.append(QPointF(rx, ry))

        path = QPainterPath()
        path.moveTo(rotated_corners[0])
        for corner in rotated_corners[1:]:
            path.lineTo(corner)
        path.closeSubpath()

        if self._border_rect:
            self._scene.removeItem(self._border_rect)
        self._border_rect = QGraphicsPathItem(path)
        self._border_rect.setPen(QPen(QColor(66, 133, 244), BORDER_WIDTH, Qt.PenStyle.DashLine))
        self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
        self._scene.addItem(self._border_rect)

    def _update_border_rect(self, rect: QRectF) -> None:
        """테두리 사각형 업데이트"""
        if self._border_rect:
            if not isinstance(self._border_rect, QGraphicsRectItem):
                self._scene.removeItem(self._border_rect)
                self._border_rect = QGraphicsRectItem(rect)
                self._border_rect.setPen(QPen(QColor(66, 133, 244), BORDER_WIDTH, Qt.PenStyle.DashLine))
                self._border_rect.setBrush(Qt.BrushStyle.NoBrush)
                self._scene.addItem(self._border_rect)
            else:
                self._border_rect.setRect(rect)

    def mousePressEvent(self, event) -> None:
        """마우스 프레스 이벤트"""
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

    def mouseMoveEvent(self, event) -> None:
        """마우스 이동 이벤트"""
        if self._dragging and self._image_item:
            scene_pos = self.mapToScene(event.pos())

            if self._free_transform_mode:
                self._handle_free_transform_move(scene_pos)
                event.accept()
                return

            self._handle_resize_move(scene_pos)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def _handle_free_transform_move(self, scene_pos: QPointF) -> None:
        """자유 변형 드래그 처리"""
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

    def _handle_resize_move(self, scene_pos: QPointF) -> None:
        """리사이즈 드래그 처리"""
        delta = scene_pos - self._drag_start_pos

        new_width = self._current_width
        new_height = self._current_height

        if "right" in self._drag_handle:
            new_width = max(MIN_SIZE, int(self._current_width + delta.x()))
        elif "left" in self._drag_handle:
            new_width = max(MIN_SIZE, int(self._current_width - delta.x()))

        if "bottom" in self._drag_handle:
            new_height = max(MIN_SIZE, int(self._current_height + delta.y()))
        elif "top" in self._drag_handle:
            new_height = max(MIN_SIZE, int(self._current_height - delta.y()))

        if self._keep_ratio:
            new_width, new_height = self._apply_aspect_ratio(new_width, new_height, delta)

        self.size_changed.emit(new_width, new_height)

    def _apply_aspect_ratio(self, width: int, height: int, delta: QPointF) -> tuple[int, int]:
        """비율 유지 적용"""
        if self._is_horizontal_only_resize():
            return width, int(width / self._original_aspect)

        if self._is_vertical_only_resize():
            return int(height * self._original_aspect), height

        if self._is_corner_resize():
            if abs(delta.x()) > abs(delta.y()):
                return width, int(width / self._original_aspect)
            else:
                return int(height * self._original_aspect), height

        return width, height

    def _is_horizontal_only_resize(self) -> bool:
        """가로만 리사이즈하는지 확인"""
        return ("left" in self._drag_handle or "right" in self._drag_handle) and \
               ("top" not in self._drag_handle and "bottom" not in self._drag_handle)

    def _is_vertical_only_resize(self) -> bool:
        """세로만 리사이즈하는지 확인"""
        return ("top" in self._drag_handle or "bottom" in self._drag_handle) and \
               ("left" not in self._drag_handle and "right" not in self._drag_handle)

    def _is_corner_resize(self) -> bool:
        """코너 리사이즈인지 확인"""
        return self._drag_handle in ["top_left", "top_right", "bottom_left", "bottom_right"]

    def mouseReleaseEvent(self, event) -> None:
        """마우스 릴리즈 이벤트"""
        if self._dragging:
            self._dragging = False
            self._drag_handle = None
            self.transform_ended.emit()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def get_current_size(self) -> tuple[int, int]:
        """현재 크기 반환"""
        return self._current_width, self._current_height

    def update_display_size(self, width: int, height: int) -> None:
        """디스플레이 크기 업데이트"""
        self._current_width = width
        self._current_height = height

    def set_rotation(self, angle: float, original_size: tuple[int, int]) -> None:
        """회전 각도 및 원본 크기 설정"""
        self._rotation_angle = angle
        self._original_size = original_size
        if self._image_item and not self._free_transform_mode:
            self._update_rotated_border()
