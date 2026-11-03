from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QApplication,
    QFrame, QLabel, QHBoxLayout, QPushButton,
    QLineEdit, QGridLayout
)
from PySide6.QtGui import QColor, QFont
from caspian_surveyor.ui.caspian_theme import load_application_font
from caspian_surveyor.ui.hud_widgets import HudFactory
from caspian_surveyor.rebound.caspian_to_rebound_data_prep import CaspianDataHandler
from caspian_surveyor.rebound.rebound_adapter import ReboundAdapter
from caspian_surveyor.utils.qtthreads import run_in_background
import time
import sys


class ReboundDataDisplay(QWidget):
    def __init__(self):
        super().__init__()

        self.hud_factory = HudFactory()
        self.data_handler = CaspianDataHandler()
        self.adapter = ReboundAdapter()
        self.selected_system_payload = None

        self.panel = QFrame(self)
        self.panel.setObjectName("REBOUND")

        self.configure_window()
        self.create_labels()
        self.connect_system_lookup_signals()
        self.connect_rebound_simulation_signal()
        self.set_panel_layout()
        self.set_border_color()

        self.create_layout()

    def create_title_area(self):
        title_area = QVBoxLayout()
        title_area.setContentsMargins(10, 5, 0, 10)
        title_area.addWidget(self.title_label)
        return title_area

    def create_layout(self):
        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(5, 5, 5, 5)
        window_layout.addWidget(self.panel)

        self.setLayout(window_layout)

    def set_panel_layout(self):
        horizontal_separator = self.create_horizontal_separator()
        title_area = self.create_title_area()
        metrics_layout = self.create_metrics_layout()
        run_simulation = self.create_run_sim_separator()
        enter_system_address = self.create_system_address_textbox()

        panel_layout = QVBoxLayout()
        panel_layout.setContentsMargins(24, 10, 24, 10)
        panel_layout.setSpacing(0)
        panel_layout.addLayout(title_area) # title area layout
        panel_layout.addWidget(horizontal_separator)
        panel_layout.addStretch()
        panel_layout.addLayout(metrics_layout) # key value layout
        panel_layout.addLayout(run_simulation)
        panel_layout.addLayout(enter_system_address) # enter system address

        self.panel.setLayout(panel_layout)

    def create_system_address_textbox(self):
        enter_system_address = QHBoxLayout()
        enter_system_address.setContentsMargins(0, 10, 0, 10)
        enter_system_address.addWidget(self.system_address)
        enter_system_address.addWidget(self.submit_address)
        return enter_system_address

    def create_run_sim_separator(self):
        horizontal_separator = self.create_horizontal_separator()
        run_sim_layout = self.create_run_simulation_layout()
        run_sim_separator = QVBoxLayout()
        run_sim_separator.addWidget(horizontal_separator)
        run_sim_separator.addLayout(run_sim_layout)
        return run_sim_separator

    def create_run_simulation_layout(self):
        run_sim_layout = QHBoxLayout()
        run_sim_layout.setContentsMargins(0, 10, 0, 10)
        run_sim_layout.addWidget(self.run_simulation_label)
        run_sim_layout.addWidget(self.run_simulation_years)
        run_sim_layout.addWidget(self.run_simulation_button)

        return run_sim_layout

    def set_border_color(self):
        value_color = QColor(self.hud_factory.value_label_color)
        border_color = value_color.darker(220)

        self.panel.setStyleSheet(f"""
            QFrame#REBOUND {{
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

    def create_vertical_separator(self):
        vertical_separator = QFrame()
        vertical_separator.setFrameShape(QFrame.Shape.VLine)
        vertical_separator.setFrameShadow(QFrame.Shadow.Sunken)
        return vertical_separator

    def create_horizontal_separator(self):
        horizontal_separator = QFrame()
        horizontal_separator.setFrameShape(QFrame.Shape.HLine)
        horizontal_separator.setFrameShadow(QFrame.Shadow.Sunken)
        return horizontal_separator

    def create_metrics_layout(self):
        vertical_separator = self.create_vertical_separator()

        metrics_layout = QGridLayout()
        metrics_layout.setContentsMargins(5, 10, 10, 5)
        metrics_layout.setVerticalSpacing(12)
        metrics_layout.setHorizontalSpacing(15)

        metrics_layout.addWidget(self.status_key_label, 0, 0)
        metrics_layout.addWidget(self.status_value_label, 0, 2)

        metrics_layout.addWidget(self.system_address_label, 1, 0)
        metrics_layout.addWidget(self.system_address_value, 1, 2)

        metrics_layout.addWidget(self.system_name_label, 2, 0)
        metrics_layout.addWidget(self.system_name_value, 2, 2)

        metrics_layout.addWidget(self.system_body_count_label, 3, 0)
        metrics_layout.addWidget(self.system_body_count_value, 3, 2)

        # Four rows, one continuous separator
        metrics_layout.addWidget(vertical_separator, 0, 1, 4, 1)

        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(2, 1)
        return metrics_layout

    def create_labels(self):
        self.title_label = QLabel("Caspian Surveyor // REBOUND")
        self.title_label.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 16px;
            font-weight: bold;
        """)

        self.status_key_label = QLabel("Metric")
        self.status_key_label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 16px;
            font-weight: bold;
        """)

        self.status_value_label = QLabel("Values")
        self.status_value_label.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 16px;
            font-weight: bold;
        """)
        self.status_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.system_address_label = QLabel("System Address")
        self.system_address_label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.system_address_value = QLabel("Please run a query.")
        self.system_address_value.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 12px;
            font-weight: bold;
        """)
        self.system_address_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.system_name_label = QLabel("System Name")
        self.system_name_label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.system_name_value = QLabel("Please run a query.")
        self.system_name_value.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 12px;
            font-weight: bold;
        """)
        self.system_name_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.system_body_count_label = QLabel("System Body Count")
        self.system_body_count_label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.system_body_count_value = QLabel("Please run a query.")
        self.system_body_count_value.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 12px;
            font-weight: bold;
        """)
        self.system_body_count_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.system_address = QLineEdit()
        self.system_address.setPlaceholderText("<system address>")
        self.system_address.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.submit_address = QPushButton("Fetch System Data")
        self.submit_address.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 10px;
            font-weight: bold;
        """)

        self.run_simulation_label = QLabel("Specify years to simulate:")
        self.run_simulation_label.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.run_simulation_years = QLineEdit("100000")
        self.run_simulation_years.setStyleSheet(f"""
            color: {self.hud_factory.key_label_color};
            font-size: 12px;
            font-weight: bold;
        """)

        self.run_simulation_button = QPushButton("Run Simulation")
        self.run_simulation_button.setStyleSheet(f"""
            color: {self.hud_factory.value_label_color};
            font-size: 10px;
            font-weight: bold;
        """)

    def connect_system_lookup_signals(self) -> None:
        self.submit_address.clicked.connect(self.fetch_system_info)
        self.system_address.textChanged.connect(
            self.invalidate_selected_system
        )

    def connect_rebound_simulation_signal(self) -> None:
        self.run_simulation_button.clicked.connect(
            self.run_rebound_simulation
        )
        self.system_address.textChanged.connect(
            self.invalidate_selected_system
        )

    def invalidate_selected_system(self) -> None:
        self.selected_system_payload = None

    def configure_window(self):
        self.setWindowTitle("Caspian Surveyor // REBOUND")
        self.setFixedWidth(750)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def run_rebound_simulation(self) -> None:
        sim_years = self.run_simulation_years.text().strip()

        if not sim_years:
            return

        if not sim_years.isdecimal():
            return

        if int(sim_years) <= 0:
            return

        if self.selected_system_payload is None:
            return

        system_address = (
            self.selected_system_payload.system.system_address
        )

        run_in_background(
            self.adapter.prepare_system_simulation,
            system_address,
            int(sim_years),
            on_complete=self.simulation_finished
        )

    def simulation_finished(self, result) -> None:
        print("REBOUND simulation completed.")
        print(f"Result: {result}")

    def fetch_system_info(self) -> None:
        user_value = self.system_address.text().strip()

        if not user_value:
            self.system_name_value.setText("Please enter a system address.")
            return

        if not user_value.isdecimal():
            self.system_name_value.setText("Invalid system address.")
            return
        payload = self.data_handler._get_fullstarsystempayload(int(user_value))

        self.selected_system_payload = payload

        if self.selected_system_payload is None:
            self.system_name_value.setText("System not found in archive.")
            return

        system_name = self.selected_system_payload.system.system_name
        system_address = self.selected_system_payload.system.system_address
        system_body_count = self.selected_system_payload.system.system_body_count

        self.system_address_value.setText(f"{system_address}")
        self.system_name_value.setText(f"{system_name}")
        self.system_body_count_value.setText(f"{system_body_count}")

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_window_mode()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def toggle_window_mode(self) -> None:
        is_frameless = bool(
            self.windowFlags() & Qt.WindowType.FramelessWindowHint
        )

        self.setWindowFlag(
            Qt.WindowType.FramelessWindowHint,
            not is_frameless
        )
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font_family = load_application_font()
    app.setFont(QFont(font_family))
    rebound_widget = ReboundDataDisplay()
    rebound_widget.show()
    sys.exit(app.exec())