from math import sqrt

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget
from caspian_surveyor.ui import caspian_theme as caspian_theme
from caspian_surveyor.ui.hud_widgets import HudFactory
from caspian_surveyor.humanity_relocation_project.humanity_relocation_project import HumanityRelocationProject
from caspian_surveyor.ui.overlay_adapter import OverlayAdapter
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
import logging

logger = logging.getLogger(__name__)


class HudExtension(QWidget):
    def __init__(self, main_panel):
        self.hud_factory = HudFactory()
        self.hrp = HumanityRelocationProject()
        self.dos_value = 0
        self.extension_counter = 0
        super().__init__()

        self.hud = main_panel

        self._set_widget_attributes()
        self._set_theme()
        self._create_extension_layout()
        caspian_theme.load_application_font()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        width = float(self.width())
        height = float(self.height())

        path.moveTo(75, 0)                  # Top-left, moving clockwise.
        path.lineTo(width - 75, 0)          # 75px from right width boundary
        path.lineTo(width - 100, height)    # Sloped right edge.
        path.lineTo(100, height)            # Narrower bottom edge.
        path.lineTo(75, 0)                  # left edge.
        path.closeSubpath()

        pen = QPen(self.border_color)
        pen.setWidthF(1.25)

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

    def set_label_shadow(self, label: QLabel) -> None:
        shadow = QGraphicsDropShadowEffect(label)
        shadow.setBlurRadius(2)
        shadow.setColor(QColor(0, 0, 0, 255))
        shadow.setXOffset(1)
        shadow.setYOffset(1)

        label.setGraphicsEffect(shadow)

    def _create_extension_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.extension_label = QLabel()
        self.extension_label.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        layout.addWidget(self.extension_label)


    def _update_distance_from_sol_label(self, current_system: FullStarSystemPayload):
        position_x, position_y, position_z = current_system.system.system_position

        self.dos_value = self._get_distance_from_sol(position_x, position_y, position_z)
        self.extension_label.setText(f"Distance from Sol:  {self.dos_value} LY")

        self.set_label_shadow(self.extension_label)
        return self.extension_label

    def _get_distance_from_sol(self, posx, posy, posz) -> float:
        return round(sqrt(posx**2 + posy**2 + posz**2), 4)

    def _update_hrp_label(self, current_system):
        report = self.hrp.scorer.evaluate_system(current_system, self.dos_value)
        self.extension_label.setText(
            f"Current System Score:  {report.final_system_score}/100"
        )

    def cycle_extension_qwidget(self, current_system):
        if self.extension_counter == 1:
            self.extension_counter = 0
            return self._update_hrp_label(current_system)

        else:
            self.extension_counter = 1
            return self._update_distance_from_sol_label(current_system)