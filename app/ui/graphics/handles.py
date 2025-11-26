"""리사이즈 핸들 컴포넌트"""
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPen, QColor, QCursor

HANDLE_SIZE = 10


class ResizeHandle(QGraphicsRectItem):
    """이미지 리사이즈/변형을 위한 핸들"""

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
        """핸들 위치에 따른 커서 모양 반환"""
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
