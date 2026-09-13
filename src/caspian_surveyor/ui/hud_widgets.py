from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, 
    QStackedWidget, QSizePolicy, 
    QGraphicsDropShadowEffect, 
)
from PySide6.QtGui import QColor


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
            font-family: Eurostile;
            font-size: {self.key_font_size}px;
            font-weight: 1000;
            letter-spacing: 1px;
        """)

        self.val_label.setStyleSheet(f"""
            color: {self.val_label_font_color};
            font-family: Eurostile;
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