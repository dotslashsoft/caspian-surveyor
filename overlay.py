import sys
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, 
    QVBoxLayout, QFrame, QStackedWidget, QSizePolicy
)
import data_structures
import keyboard
import logging
import bootstrap.cs_log_factory as cs_log_factory

logger = logging.getLogger(__name__)
log_manager = cs_log_factory.LogManager()
log_manager.set_log_config()

class MetricWidget(QWidget):
    def __init__(
        self,
        key: str,
        default_value: str | int | float = "--"
    ):
        super().__init__()

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.key_label = QLabel(key)
        self.key_label.setStyleSheet("""
            color: #7d8b99;
            font-family: Eurostile;
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 1px;
        """)

        self.val_label = QLabel(str(default_value))
        self.val_label.setStyleSheet("""
            color: #56cffc;
            font-family: Eurostile;
            font-size: 13px;
            font-weight: bold;
        """)

        layout.addWidget(self.key_label)
        layout.addWidget(self.val_label)


    def set_value(self, value: str | int | float | None):
        self.val_label.setText(str(value))

        if value is None:
            self.val_label.setText("--")
        else:
            self.val_label.setText(str(value))

class JournalWorker(QtCore.QObject):
    system_updated = QtCore.Signal(object)

    def run(self):
        print("Journal worker is running")
        logger.info("Journal worker is running")


class SystemInfoOverlay(QWidget):
    toggle_requested = QtCore.Signal()
    exit_requested = QtCore.Signal()
    cycle_next = QtCore.Signal()
    cycle_previous = QtCore.Signal()
    cycle_default = QtCore.Signal()

    PANEL_STYLE = """
        QFrame#HUDPanel {
            background-color: rgba(0, 0, 0, 100);
            border-top: 1px solid #002e4d;
            border-bottom: 1px solid #004d80;
            border-radius: 8px;
            border-left: none;
            border-right: none;
            font-family: Eurostile;
        }
    """

    def __init__(self):
        super().__init__()

        self._connect_signals()
        self._register_hotkeys()
        self._load_initial_data()
        self._configure_window()
        self._build_ui()
        self._start_background_services()

    def refresh_system_data(self):
        ui_data = data_structures.load_latest_system_record()

        if ui_data is None:
            return

        system_changed = (
            self.ui_data is None
            or ui_data.system.address != self.ui_data.system.address
        )

        self.ui_data = ui_data
        self.planetary_bodies = ui_data.planetary_bodies

        if system_changed:
            self.current_body_index = 0

            if self.planetary_bodies:
                self.update_body_display()

        self.metric_system.set_value(ui_data.system.name.upper())
        self.metric_planets.set_value(ui_data.summary.planets)
        self.metric_elw.set_value(ui_data.summary.earthlike_worlds)
        self.metric_tfww.set_value(ui_data.summary.tf_water_worlds)
        self.metric_tfhmc.set_value(ui_data.summary.tf_hmc)
        self.metric_water_world.set_value(ui_data.summary.water_worlds)
        self.metric_hmc.set_value(ui_data.summary.hmc)
        self.metric_landable.set_value(ui_data.summary.landable)

        self.position_top_center()

    def _load_initial_data(self):
        self.ui_data = data_structures.load_latest_system_record()

        if self.ui_data is not None:
            self.planetary_bodies = self.ui_data.planetary_bodies
        else:
            self.planetary_bodies = []

        self.current_body_index = 0

    def _configure_window(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        self.display_stack = QStackedWidget()

        self.system_page = self._build_system_page()
        self.body_page = self._build_body_page()

        assert self.system_page is not None
        self.display_stack.addWidget(self.system_page)
        self.display_stack.addWidget(self.body_page)
        self.display_stack.setCurrentIndex(0)

        outer_layout.addWidget(self.display_stack)


    def _connect_signals(self):
        self.toggle_requested.connect(self.toggle_widget)
        self.exit_requested.connect(self.exit_overlay)

        self.cycle_next.connect(self.cycle_display_next)
        self.cycle_previous.connect(self.cycle_display_previous)
        self.cycle_default.connect(self.cycle_display_default)


    def _register_hotkeys(self):
        keyboard.add_hotkey(
            "ctrl+shift+m",
            self.toggle_requested.emit
        )

        keyboard.add_hotkey(
            "ctrl+shift+e",
            self.exit_requested.emit
        )

        keyboard.add_hotkey(
            "ctrl+alt+right",
            self.cycle_next.emit
        )

        keyboard.add_hotkey(
            "ctrl+alt+left",
            self.cycle_previous.emit
        )

        keyboard.add_hotkey(
            "ctrl+alt+home",
            self.cycle_default.emit
        )


    def _build_system_page(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        title_widget = self._create_title_widget()

        hud_layout.addWidget(title_widget)
        hud_layout.addWidget(self._create_separator())

        if self.ui_data == None:
            return
        
        self.metric_system = MetricWidget(
            "SYSTEM",
            self.ui_data.system.name.upper()
        )

        self.metric_planets = MetricWidget(
            "PLANETS",
            self.ui_data.summary.planets
        )

        self.metric_elw = MetricWidget(
            "ELW",
            self.ui_data.summary.earthlike_worlds
        )

        self.metric_tfww = MetricWidget(
            "TFWW",
            self.ui_data.summary.tf_water_worlds
        )

        self.metric_tfhmc = MetricWidget(
            "TFHMC",
            self.ui_data.summary.tf_hmc
        )

        self.metric_water_world = MetricWidget(
            "WW",
            self.ui_data.summary.water_worlds
        )

        self.metric_hmc = MetricWidget(
            "HMC",
            self.ui_data.summary.hmc
        )

        self.metric_landable = MetricWidget(
            "LANDABLE",
            self.ui_data.summary.landable
        )

        metrics = [
            self.metric_system,
            self.metric_planets,
            self.metric_elw,
            self.metric_tfww,
            self.metric_tfhmc,
            self.metric_water_world,
            self.metric_hmc,
            self.metric_landable,
        ]

        self._add_metrics(hud_layout, metrics)

        page_layout.addWidget(panel)

        self.system_panel = panel
        panel = self._create_hud_panel()
        # print(self.metric_system.val_label.font().family())
        # print(self.metric_system.key_label.font().family())

        return page

    def _build_body_page(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        self.metric_body_name = MetricWidget("PLANET", "--")
        self.metric_body_class = MetricWidget("CLASS", "--")
        self.metric_tf_state = MetricWidget("TF", "--")
        self.metric_body_signals = MetricWidget("SIGNALS", "--")
        self.metric_body_temp = MetricWidget("TEMP K", "--")
        self.metric_body_dss = MetricWidget("DSS SCAN", False)

        metrics = [
            self.metric_body_name,
            self.metric_body_class,
            self.metric_tf_state,
            self.metric_body_signals,
            self.metric_body_temp,
            self.metric_body_dss
        ]

        self._add_metrics(hud_layout, metrics)

        page_layout.addWidget(panel)
        panel = self._create_hud_panel()

        return page

    def _build_exobio_page(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        self.metric_body_name = MetricWidget("PLANET", "--")
        self.metric_exobio_signals = MetricWidget("EXOSIGNALS", "--")
        self.metric_exobio_genus = MetricWidget("GENUS", "--")
        self.metric_exobio_species = MetricWidget("SPECIES", "--")
        self.metric_exibio_variant = MetricWidget("VARIANT", "--")

        metrics = [
            self.metric_body_name,
            self.metric_exobio_signals,
            self.metric_exobio_genus,
            self.metric_exobio_species,
            self.metric_exibio_variant,
        ]

        self._add_metrics(hud_layout, metrics)

        page_layout.addWidget(panel)
        panel = self._create_hud_panel()

        return page

    def _create_hud_panel(self):
        panel = QFrame()
        panel.setObjectName("HUDPanel")
        panel.setStyleSheet(self.PANEL_STYLE)
        return panel


    def _add_metrics(self, layout, metrics):
        for index, metric in enumerate(metrics):
            layout.addWidget(metric)

            if index < len(metrics) - 1:
                layout.addWidget(self._create_separator())

    def _create_title_widget(self):
        title_widget = QWidget()

        title_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(title_widget)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(6)

        app_title = QLabel("CASPIAN")
        app_title.setStyleSheet(
            "color: #56cffc;"
            "font-size: 12px;"
            "font-weight: 800;"
            "letter-spacing: 2px;"
            "font-family: Eurostile;"
        )

        app_sub = QLabel("SURVEYOR")
        app_sub.setStyleSheet(
            "color: #7d8b99;"
            "font-size: 9px;"
            "font-weight: bold;"
            "letter-spacing: 1px;"
            "font-family: Eurostile;"
        )

        layout.addWidget(app_title)
        layout.addWidget(app_sub)

        return title_widget

    def _start_background_services(self):
        self.journal_thread = QtCore.QThread()
        self.journal_worker = JournalWorker()

        self.journal_worker.moveToThread(self.journal_thread)
        self.journal_thread.started.connect(
            self.journal_worker.run
        )

        self.journal_thread.start()

        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(
            self.refresh_system_data
        )
        self.update_timer.start(5000)

    def toggle_widget(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def exit_overlay(self):
        app_instance = QApplication.instance()

        if app_instance is not None:
            app_instance.quit()
        else:
            print("Error: QApplication has not been initialized yet.")

    def cycle_display_next(self):
        if not self.planetary_bodies:
            return

        self.current_body_index = (
            self.current_body_index + 1
        ) % len(self.planetary_bodies)

        self.update_body_display()
        self.display_stack.setCurrentIndex(1)

    def cycle_display_previous(self):
        if not self.planetary_bodies:
            return

        self.current_body_index = (
            self.current_body_index - 1
        ) % len(self.planetary_bodies)

        self.update_body_display()
        self.display_stack.setCurrentIndex(1)

    def cycle_display_default(self):
        self.display_stack.setCurrentIndex(0)

    def update_body_display(self):
        body = self.planetary_bodies[self.current_body_index]
        self.metric_body_name.set_value(body.body_name)

        self.metric_body_class.set_value(body.planet_class)

        if body.signals:
            signal_text = "\n".join(
                f"{signal.type_localised}: {signal.count}"
                for signal in body.signals
            )

            self.metric_body_signals.set_value(signal_text)
        else:
            self.metric_body_signals.set_value("--")

        if body.terraform_state:
            self.metric_tf_state.set_value(body.terraform_state)
        else:
            self.metric_tf_state.set_value("--")
            

        self.metric_body_temp.set_value(f"{body.surface_temperature:.2f}")
        self.metric_body_dss.set_value(body.dss_scan_complete)

    def _create_separator(self) -> QFrame:
        """Creates a subtle vertical divider line between metrics."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("color: rgba(0, 122, 124, 25);")
        return line

    def position_top_center(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        self.resize(self.sizeHint())
        x = (screen_geometry.width() - self.width()) // 2
        y = 15
        self.move(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = SystemInfoOverlay()
    overlay.show()
    overlay.position_top_center()
    sys.exit(app.exec())