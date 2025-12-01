"""포토샵 스타일 자유변형 프리뷰 뷰"""
from typing import Optional

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter, QPainterPath

from .handles import CornerHandle
from .items import TransformableImageItem

BORDER_WIDTH = 1.5
PADDING_RATIO = 0.08
CORNER_NAMES = ["top_left", "top_right", "bottom_right", "bottom_left"]


class FreeTransformView(QGraphicsView):
    """포토샵 스타일 자유변형 뷰

    4개의 코너 핸들을 드래그하여 원근 변형 적용
    """

    perspective_changed = Signal(list)
    transform_started = Signal()
    transform_ended = Signal()

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
        self.setStyleSheet("background-color: #1a1a1a; border: none;")

        self._image_item: Optional[TransformableImageItem] = None
        self._handles: dict[str, CornerHandle] = {}
        self._border_path: Optional[QGraphicsPathItem] = None

        self._corners: dict[str, QPointF] = {}
        self._dragging = False
        self._drag_corner: Optional[str] = None

    def set_image(self, pixmap: QPixmap, reset_corners: bool = False) -> None:
        """이미지 설정"""
        saved_corners = None if reset_corners else self._corners.copy()

        self._scene.clear()
        self._handles.clear()
        self._border_path = None
        self._corners.clear()

        if pixmap.isNull():
            return

        self._image_item = TransformableImageItem(pixmap)
        self._scene.addItem(self._image_item)

        rect = self._image_item.boundingRect()
        w, h = rect.width(), rect.height()

        if saved_corners and len(saved_corners) == 4:
            self._corners = saved_corners
        else:
            self._corners = {
                "top_left": QPointF(0, 0),
                "top_right": QPointF(w, 0),
                "bottom_right": QPointF(w, h),
                "bottom_left": QPointF(0, h),
            }

        self._create_border()
        self._create_handles()
        self._update_visuals()
        self._fit_view()

    def _create_border(self) -> None:
        """테두리 경로 생성"""
        self._border_path = QGraphicsPathItem()
        self._border_path.setPen(QPen(QColor(0, 120, 215), BORDER_WIDTH))
        self._border_path.setZValue(50)
        self._scene.addItem(self._border_path)

    def _create_handles(self) -> None:
        """4개 코너 핸들 생성"""
        for corner in CORNER_NAMES:
            handle = CornerHandle(corner)
            self._scene.addItem(handle)
            self._handles[corner] = handle

    def _update_visuals(self) -> None:
        """테두리와 핸들 위치 업데이트"""
        if not self._corners or not self._border_path:
            return

        path = QPainterPath()
        corners_list = [self._corners[name] for name in CORNER_NAMES]
        path.moveTo(corners_list[0])
        for corner in corners_list[1:]:
            path.lineTo(corner)
        path.closeSubpath()
        self._border_path.setPath(path)

        for name, handle in self._handles.items():
            if name in self._corners:
                handle.setPos(self._corners[name])

    def _fit_view(self) -> None:
        """뷰를 이미지에 맞게 조절"""
        rect = self._scene.itemsBoundingRect()
        padding_x = rect.width() * PADDING_RATIO
        padding_y = rect.height() * PADDING_RATIO
        padded = rect.adjusted(-padding_x, -padding_y, padding_x, padding_y)
        self._scene.setSceneRect(padded)
        self.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)

    def mousePressEvent(self, event) -> None:
        """마우스 프레스 - 핸들 드래그 시작"""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        scene_pos = self.mapToScene(event.pos())

        for corner, handle in self._handles.items():
            if handle.contains(handle.mapFromScene(scene_pos)):
                self._dragging = True
                self._drag_corner = corner
                self.transform_started.emit()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """마우스 이동 - 코너 드래그"""
        if not self._dragging or not self._drag_corner:
            super().mouseMoveEvent(event)
            return

        scene_pos = self.mapToScene(event.pos())
        self._corners[self._drag_corner] = scene_pos
        self._update_visuals()
        self._emit_corners()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        """마우스 릴리즈 - 드래그 종료"""
        if self._dragging:
            self._dragging = False
            self._drag_corner = None
            self.transform_ended.emit()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _emit_corners(self) -> None:
        """현재 코너 좌표를 시그널로 전송"""
        if not self._image_item:
            return

        corners = [
            (self._corners[name].x(), self._corners[name].y())
            for name in CORNER_NAMES
        ]
        self.perspective_changed.emit(corners)

    def reset_corners(self) -> None:
        """코너를 원래 위치로 초기화"""
        if not self._image_item:
            return

        rect = self._image_item.boundingRect()
        w, h = rect.width(), rect.height()

        self._corners = {
            "top_left": QPointF(0, 0),
            "top_right": QPointF(w, 0),
            "bottom_right": QPointF(w, h),
            "bottom_left": QPointF(0, h),
        }
        self._update_visuals()
        self._emit_corners()

    def get_corners(self) -> list[tuple[float, float]]:
        """현재 코너 좌표 반환"""
        return [
            (self._corners[name].x(), self._corners[name].y())
            for name in CORNER_NAMES
        ]

    def set_corners(self, corners: list[tuple[float, float]]) -> None:
        """코너 좌표 설정"""
        if len(corners) != 4:
            return

        for i, name in enumerate(CORNER_NAMES):
            self._corners[name] = QPointF(corners[i][0], corners[i][1])
        self._update_visuals()


# 하위 호환성을 위한 래퍼 클래스
class PreviewGraphicsView(FreeTransformView):
    """하위 호환성을 위한 래퍼"""

    size_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_width = 0
        self._current_height = 0

    def set_image(self, pixmap: QPixmap, reset_transform: bool = False) -> None:
        super().set_image(pixmap, reset_corners=reset_transform)
        if not pixmap.isNull():
            self._current_width = pixmap.width()
            self._current_height = pixmap.height()

    def set_free_transform_mode(self, enabled: bool) -> None:
        """자유변형 모드는 항상 활성화 (하위 호환용)"""
        pass

    def set_keep_ratio(self, keep: bool) -> None:
        """비율 유지 설정 (하위 호환용 - 미사용)"""
        pass

    def reset_corner_offsets(self) -> None:
        """코너 초기화 (하위 호환용)"""
        self.reset_corners()

    def set_uniform_offset(self, offset: float) -> None:
        """균일 오프셋 (하위 호환용)"""
        if not self._image_item:
            return

        rect = self._image_item.boundingRect()
        w, h = rect.width(), rect.height()

        self._corners = {
            "top_left": QPointF(offset, offset),
            "top_right": QPointF(w - offset, offset),
            "bottom_right": QPointF(w - offset, h - offset),
            "bottom_left": QPointF(offset, h - offset),
        }
        self._update_visuals()
        self._emit_corners()

    def update_display_size(self, width: int, height: int) -> None:
        """디스플레이 크기 업데이트 (하위 호환용)"""
        self._current_width = width
        self._current_height = height

    def set_rotation(self, angle: float, original_size: tuple[int, int]) -> None:
        """회전 설정 (하위 호환용 - 자유변형에서는 미사용)"""
        pass

    def get_current_size(self) -> tuple[int, int]:
        """현재 크기 반환"""
        return self._current_width, self._current_height
