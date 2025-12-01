"""포토샵 스타일 자유변형 핸들"""
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPen, QColor, QCursor

HANDLE_SIZE = 8
HANDLE_HOVER_SIZE = 10


class CornerHandle(QGraphicsRectItem):
    """자유변형용 코너 핸들 (포토샵 스타일)"""

    def __init__(self, corner: str, parent=None):
        super().__init__(parent)
        self.corner = corner
        self._is_hovered = False
        self._size = HANDLE_SIZE

        self._update_rect()
        self._apply_style()

        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setZValue(100)

    def _update_rect(self):
        half = self._size / 2
        self.setRect(-half, -half, self._size, self._size)

    def _apply_style(self):
        if self._is_hovered:
            self.setBrush(QBrush(QColor(0, 120, 215)))
            self.setPen(QPen(QColor(255, 255, 255), 2))
        else:
            self.setBrush(QBrush(QColor(255, 255, 255)))
            self.setPen(QPen(QColor(0, 120, 215), 1.5))

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self._size = HANDLE_HOVER_SIZE
        self._update_rect()
        self._apply_style()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self._size = HANDLE_SIZE
        self._update_rect()
        self._apply_style()
        super().hoverLeaveEvent(event)


# 하위 호환성을 위한 별칭
ResizeHandle = CornerHandle
