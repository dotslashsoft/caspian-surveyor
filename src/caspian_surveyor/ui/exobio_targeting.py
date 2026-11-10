
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class TargetingOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.bounding_boxes = []

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

    def update_detections(self, bounding_boxes):
        self.bounding_boxes = list(bounding_boxes)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(0, 230, 230)
        painter.setPen(QPen(color, 1))

        for x, y, width, height in self.bounding_boxes:
            corner = min(12, width // 3, height // 3)

            painter.fillRect(
                x, y, width, height,
                QColor(0, 230, 230, 51)
            )

            # top left
            painter.drawLine(x, y, x + corner, y)
            painter.drawLine(x, y, x, y + corner)

            # top right
            painter.drawLine(
                x + width, y,
                x + width - corner, y
            )
            painter.drawLine(
                x + width, y,
                x + width, y + corner
            )

            # bottom left
            painter.drawLine(
                x, y + height,
                x + corner, y + height
            )
            painter.drawLine(
                x, y + height,
                x, y + height - corner
            )

            # bottom right
            painter.drawLine(
                x + width, y + height,
                x + width - corner, y + height
            )
            painter.drawLine(
                x + width, y + height,
                x + width, y + height - corner
            )

        painter.end()
