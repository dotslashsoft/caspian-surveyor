from math import sqrt

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from caspian_surveyor.ui import caspian_theme as caspian_theme
from caspian_surveyor.ui.hud_widgets import HudFactory
from caspian_surveyor.humanity_relocation_project.humanity_relocation_project import HumanityRelocationProject
from caspian_surveyor.ui.overlay_adapter import OverlayAdapter
import logging

logger = logging.getLogger(__name__)


class HudExtension(QWidget):
    def __init__(self, main_panel):
        self.hud_factory = HudFactory()
        self.hrp = HumanityRelocationProject()
        self.overlay_adapter = OverlayAdapter()
        super().__init__()

        self.hud = main_panel

        self._set_widget_attributes()
        self._set_theme()
        self._create_extension_layout()
        caspian_theme.load_application_font()
        self.hud.adjustSize()

        logger.debug(
            "HUD geometry: %s | visible: %s | sizeHint: %s",
            self.hud.geometry(),
            self.hud.isVisible(),
            self.hud.sizeHint()
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = float(self.width())
        height = float(self.height())

        path = QPainterPath()

        # Top-left, moving clockwise.
        path.moveTo(75, 0)
        path.lineTo(width - 75, 0)

        # Sloped right edge.
        path.lineTo(width - 100, height)

        # Narrower bottom edge.
        path.lineTo(100, height)

        # left edge.
        path.lineTo(75, 0)

        path.closeSubpath()

        pen = QPen(self.border_color)
        pen.setWidthF(1.0)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        painter.setPen(pen)
        painter.setBrush(self.background_color)
        painter.drawPath(path)

    def _set_widget_attributes(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def _set_theme(self):
        self.value_color = QColor(self.hud_factory.value_label_color)
        self.key_color = QColor(self.hud_factory.key_label_color)

        self.border_color = self.value_color.darker(220)
        self.border_color.setAlpha(220)

        self.background_color = QColor(0, 0, 0, 220)

    def _create_extension_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        current_system = self._get_current_system_payload()
        dos = self._get_distance_from_sol(current_system)

        self.label = QLabel(f"Distance from Sol: {dos} LY")
        self.label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: 750;
        """)

        layout.addWidget(self.label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _get_current_system_payload(self):
        current_system = self.overlay_adapter.call_load_new_system_record()
        assert current_system is not None
        return current_system.system.system_position

    def _get_distance_from_sol(self, system_position: list[float]) -> float:
        position_x, position_y, position_z = system_position
        return round(sqrt(position_x**2 + position_y**2 + position_z**2), 4)