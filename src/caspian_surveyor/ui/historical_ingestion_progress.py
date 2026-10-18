import sys

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QProgressBar, QFrame, QSizePolicy, QLabel, QHBoxLayout
from PySide6.QtGui import QColor
from caspian_surveyor.ui.hud_widgets import HudFactory

class HistoryIngestionSignals(QObject):
    progress = Signal(int, int, int)
    finished = Signal()
    failed = Signal(str)

class HistoryProgressbar(QWidget):
    def __init__(self):
        super().__init__()

        self.hud_factory = HudFactory()

        self.setWindowTitle("Caspian Surveyor - Historical Ingestion")
        self.setFixedHeight(175)
        self.setFixedWidth(750)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.panel = QFrame(self)
        self.panel.setObjectName("historyPanel")

        value_color = QColor(self.hud_factory.value_label_color)
        border_color = value_color.darker(220)

        self.panel.setStyleSheet(f"""
            QFrame#historyPanel {{
                background-color: rgba(0, 0, 0, 220);

                border: 1px solid rgba(
                    {border_color.red()},
                    {border_color.green()},
                    {border_color.blue()},
                    220
                );

                border-radius: 12px;
            }}
        """)

        self.title_label = QLabel("HISTORICAL EXPLORATION ARCHIVE")
        self.title_label.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 16px;
            font-weight: bold;
        """)

        self.status_key_label = QLabel("SYSTEMS PROCESSED")
        self.status_key_label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.status_value_label = QLabel("Preparing archive...")
        self.status_value_label.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.progress_bar = QProgressBar(self.panel)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)

        self.apply_caspian_style()

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        status_layout.addWidget(self.status_key_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_value_label)

        panel_layout = QVBoxLayout()
        panel_layout.setContentsMargins(24, 20, 24, 20)
        panel_layout.setSpacing(10)

        panel_layout.addWidget(self.title_label)
        panel_layout.addStretch()
        panel_layout.addLayout(status_layout)
        panel_layout.addWidget(self.progress_bar)
        panel_layout.addStretch()

        self.panel.setLayout(panel_layout)

        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(10, 10, 10, 10)
        window_layout.addWidget(self.panel)

        self.setLayout(window_layout)

    def apply_caspian_style(self) -> None:
        value_color = QColor(self.hud_factory.value_label_color)
        border_color = value_color.darker(220)

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(0, 0, 0, 220);

                border: 1px solid rgba(
                    {border_color.red()},
                    {border_color.green()},
                    {border_color.blue()},
                    220
                );

                border-radius: 6px;

                color: {self.hud_factory.key_label_color};
                font-size: 12px;
                font-weight: bold;

                text-align: center;
                min-height: 24px;
            }}

            QProgressBar::chunk {{
                background-color: {self.hud_factory.value_label_color};
                border-radius: 5px;
            }}
        """)

    @Slot(int, int, int)
    def update_progress_bar(
        self,
        processed_system_count: int,
        _persisted_system_count: int,
        total_system_count: int,
    ) -> None:

        self.progress_bar.setRange(0, total_system_count)
        self.progress_bar.setValue(processed_system_count)

        if total_system_count:
            progress_percent = int(
                processed_system_count / total_system_count * 100
            )
        else:
            progress_percent = 0

        self.status_value_label.setText(
            f"{processed_system_count} / "
            f"{total_system_count} "
            f"({progress_percent}%)"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    progress_window = HistoryProgressbar()
    progress_window.show()
    sys.exit(app.exec())