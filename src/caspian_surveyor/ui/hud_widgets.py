from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QWidget, QLabel, QVBoxLayout, 
    QStackedWidget, QSizePolicy, 
    QGraphicsDropShadowEffect, 
)
from PySide6.QtGui import QColor
from caspian_surveyor.ui.custom_color_picker import ConfigFileHandler
import json


class CurrentPageStackedWidget(QStackedWidget):
    def sizeHint(self):
        current_widget = self.currentWidget()
        if current_widget is not None:
            return current_widget.sizeHint()

        return super().sizeHint()

    def minimumSizeHint(self):
        current_widget = self.currentWidget()
        if current_widget is not None:
            return current_widget.minimumSizeHint()

        return super().minimumSizeHint()


class MetricWidget(QWidget):
    """
    Reusable widget for displaying a labeled metric.

    Renders a small, muted key label above a larger, highlighted value label.
    Uses a fixed vertical size policy to keep metric displays visually
    consistent within the overlay.
    """
    def __init__(
        self,
        key: str,
        default_value: str | int | float = "--",
        key_font_size: int = 10,
        key_label_font_color: str = "#a2a5a7",
        val_label_font_color: str = "#56cffc"
    ):
        """
        Initializes the MetricWidget's labels and styles.

        Args:
            key: The text title/label for the metric.
            default_value: The starting value to display. Defaults to "--".
            key_font_size: Font size in pixels for the key label. Defaults to 10.
            TODO: I wonder why I haven't implemented value_font_size
        """    
        super().__init__()
        self.key_font_size = key_font_size
        self.key_label_font_color = key_label_font_color
        self.val_label_font_color = val_label_font_color

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.key_label = QLabel(key)
        self.val_label = QLabel(str(default_value))

        self.apply_colors()

        self.set_label_shadow(self.key_label)
        self.set_label_shadow(self.val_label)

        layout.addWidget(self.key_label)
        layout.addWidget(self.val_label)

    def apply_colors(self) -> None:
        self.key_label.setStyleSheet(f"""
            color: {self.key_label_font_color};
            font-size: {self.key_font_size}px;
            font-weight: 1000;
            letter-spacing: 1px;
        """)

        self.val_label.setStyleSheet(f"""
            color: {self.val_label_font_color};
            font-size: 12px;
            font-weight: bold;
        """)

    def set_colors(self, key_label_font_color: str, val_label_font_color: str) -> None:
        self.key_label_font_color = key_label_font_color
        self.val_label_font_color = val_label_font_color

        self.apply_colors()

    def set_label_shadow(self, label: QLabel) -> None:
        shadow = QGraphicsDropShadowEffect(label)

        shadow.setBlurRadius(2)
        shadow.setColor(QColor(0, 0, 0, 255))
        shadow.setXOffset(1)
        shadow.setYOffset(1)

        label.setGraphicsEffect(shadow)


    def set_value(self, value: str | int | float | None):
        """
        Updates the metric value label text.

        Args:
            value: The data to display. If None, displays default "--".
        """

        if value is None:
            self.val_label.setText("--")
        else:
            self.val_label.setText(str(value))

    def set_label(self, value: str | int | float | None):
        """
        Updates the key label text.

        Args:
            value: The data to display. If None, displays default "--".
        """

        if value is None:
            self.key_label.setText("--")
        else:
            self.key_label.setText(str(value))


class HudFactory:

    def __init__(self) -> None:
        self.hud_panels = []
        self.panel_glow_effects = []

        self.overlay_config_path = ConfigFileHandler().OVERLAY_CONFIG
        self.load_overlay_config()

    def load_overlay_config(self) -> None:
        with self.overlay_config_path.open("r", encoding="utf-8") as file:
            overlay_config = json.load(file)

        self.key_label_color = overlay_config["key_label_color"]
        self.value_label_color = overlay_config["value_label_color"]

    def create_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("color: rgba(0, 122, 124, 25);")
        return line

    def create_hud_page(self) -> tuple[QWidget, QHBoxLayout]:
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 6, 12, 6)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        page_layout.addWidget(panel)

        return page, hud_layout

    def get_panel_style(self) -> str:
        value_color = QColor(self.value_label_color)
        border_color = value_color.darker(220)

        return f"""
            QFrame#HUDPanel {{
                background-color: rgba(0, 0, 0, 220);

                border-top: 1px solid rgba(
                    {border_color.red()},
                    {border_color.green()},
                    {border_color.blue()},
                    220
                );

                border-bottom: 1px solid rgba(
                    {border_color.red()},
                    {border_color.green()},
                    {border_color.blue()},
                    220
                );

                border-left: none;
                border-right: none;
                border-radius: 8px;
            }}
        """
    
    def _create_hud_panel(self) -> QFrame:
        """
        Creates and styles a reusable HUD panel QFrame.

        Assigns the "HUDPanel" object name and applies PANEL_STYLE so the
        resulting frame can be used consistently across overlay display pages.

        Returns:
            The configured HUD-panel QFrame.
        """
        panel = QFrame()
        panel.setObjectName("HUDPanel")
        panel.setStyleSheet(self.get_panel_style())

        glow_color = QColor(self.value_label_color)
        glow_color.setAlpha(40)

        border_glow_effect = QGraphicsDropShadowEffect(panel)
        border_glow_effect.setColor(glow_color)
        border_glow_effect.setOffset(0, 0)
        border_glow_effect.setBlurRadius(15)

        panel.setGraphicsEffect(border_glow_effect)

        self.hud_panels.append(panel)

        self.panel_glow_effects.append(border_glow_effect)

        return panel

    def refresh_panel_colors(self) -> None:
        for panel in self.hud_panels:
            panel.setStyleSheet(self.get_panel_style())
            panel.style().unpolish(panel)
            panel.style().polish(panel)
            panel.update()

    def refresh_panel_glow_colors(self) -> None:
        glow_color = QColor(self.value_label_color)
        glow_color.setAlpha(40)

        for border_glow_effect in self.panel_glow_effects:
            border_glow_effect.setColor(glow_color)