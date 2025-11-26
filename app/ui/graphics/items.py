"""그래픽스 아이템 컴포넌트"""
from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtGui import QPixmap


class TransformableImageItem(QGraphicsPixmapItem):
    """변형 가능한 이미지 아이템"""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, False)
