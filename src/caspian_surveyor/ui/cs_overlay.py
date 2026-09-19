import sys
from PySide6 import QtCore
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QFrame, QSizePolicy,
)
import logging
import caspian_surveyor.ui.custom_color_picker as custom_color_picker
from caspian_surveyor.ui.hotkey_manager import HotkeyManager
from caspian_surveyor.ui.hud_widgets import CurrentPageStackedWidget, MetricWidget, HudFactory
from caspian_surveyor.ui.body_builder import BodyDisplayController
from caspian_surveyor.ui.data_adapter import OverlayAdapter

logger = logging.getLogger(__name__)

class SystemInfoOverlay(QWidget):
    """
    Displays and manages the Caspian Surveyor HUD overlay.

    Loads current survey data, builds and refreshes system/body display pages,
    handles overlay navigation and hotkeys, and manages visibility and
    positioning.
    """
    toggle_requested = QtCore.Signal()
    exit_requested = QtCore.Signal()
    cycle_next = QtCore.Signal()
    cycle_previous = QtCore.Signal()
    cycle_default = QtCore.Signal()
    cycle_up = QtCore.Signal()
    cycle_down = QtCore.Signal()
    toggle_legend = QtCore.Signal()
    color_picker = QtCore.Signal()

    def __init__(self):
        """
        Initializes the overlay startup sequence.

        Connects signals, registers hotkeys, loads initial survey data,
        configures and builds the HUD, and starts the HUD update timer.
        """
        self.caspian_panel = []
        self.surveyor_panel = []
        
        self.custom_color_picker = custom_color_picker.Workflow()
        self.overlay_config_path = custom_color_picker.ConfigFileHandler().OVERLAY_CONFIG
        self.hud_factory = HudFactory()
        self.body_display = BodyDisplayController(self.hud_factory)
        self.overlay_adapter = OverlayAdapter()
        super().__init__()

        self._connect_signals()
        self._register_hotkeys()
        self._load_initial_data()
        self._configure_window()
        self._build_ui()
        self.refresh_overlay_colors()
        self._start_update_timer()

        self.genus_dict = {}
        self.current_index = 0

    def event(self, event):
        """
        Handles Qt layout requests that may require the overlay to resize.

        When the layout requests additional or reduced space, resizes the
        overlay to its current size hint. The resulting resize is handled by
        resizeEvent(), which repositions the overlay.
        """    
        result = super().event(event)

        if event.type() == QEvent.Type.LayoutRequest:
            self.resize(self.sizeHint())

        return result

    def resizeEvent(self, event):
        """
        Repositions the overlay after its size changes.

        Keeps the HUD centered at the top of the primary display whenever
        Qt resizes the widget.
        """
        super().resizeEvent(event)
        self.position_top_center()

    def resize_overlay_to_current_page(self):
        self.body_display.display_body_stack.updateGeometry()
        self.display_stack.updateGeometry()
        self.resize(self.sizeHint())
        self.position_top_center()

    def refresh_system_data(self):
        self.overlay_adapter.call_load_new_system_record()
        ui_data = self.overlay_adapter.full_system_data

        if ui_data is None:
            logger.debug("refresh_system_data() -> ui_data is None.")
            return

        system_changed = (
            self.ui_data is None
            or ui_data.system.system_address != self.ui_data.system.system_address
        )

        self.ui_data = ui_data
        self.planetary_bodies = ui_data.planetary_bodies

        if system_changed:
            self.current_body_index = 0
            self.current_index = 0

        if self.planetary_bodies:
            self.current_body_index %= len(self.planetary_bodies)

            body = self.planetary_bodies[self.current_body_index]
            self.body_display.update_body_display_metrics(body)

        self.metric_system_name.set_value(ui_data.system.system_name.upper())
        self.metric_system_planet_count.set_value(ui_data.summary.system_planet_count)
        self.metric_system_elw_count.set_value(ui_data.summary.system_earthlike_world_count)
        self.metric_system_tfww_count.set_value(ui_data.summary.system_tf_water_world_count)
        self.metric_system_tfhmc_count.set_value(ui_data.summary.system_tf_hmc_count)
        self.metric_system_ww_count.set_value(ui_data.summary.system_water_world_count)
        self.metric_system_hmc_count.set_value(ui_data.summary.system_hmc_count)
        self.metric_system_landable_count.set_value(ui_data.summary.system_landable_body_count)

        
    def _load_initial_data(self):
        """
        Loads the initial survey data used to populate the overlay.

        Called once during SystemInfoOverlay initialization. Loads the current
        system record, initializes the planetary-body collection, and resets
        the current body index to 0.
        """
        self.overlay_adapter.call_load_new_system_record()
        self.ui_data = self.overlay_adapter.full_system_data

        if self.ui_data is not None:
            self.planetary_bodies = self.ui_data.planetary_bodies
        else:
            self.planetary_bodies = []

        self.current_body_index = 0

    def _configure_window(self):
        """
        Configures the overlay window flags and widget attributes.

        Sets the overlay to remain on top, frameless, transparent to input,
        and visually translucent.

        Called once during SystemInfoOverlay initialization.
        """    
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
        """
        Constructs the overlay's top-level UI layout and display pages.

        Builds the system, body, and legend pages, configures the primary
        QStackedWidget, and adds the completed display components to the
        overlay layout.

        Called once during SystemInfoOverlay initialization.

        TODO: once necessary plumbing is completed, integrate _build_exobio_page()
        into the UI construction flow and update this docstring to reflect the change.
        """
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        self.display_stack = CurrentPageStackedWidget()

        self.system_page = self._build_system_page()
        self.body_page = self.body_display.body_page
        self.legend_page = self.body_display.legend_page

        assert self.system_page is not None
        self.display_stack.addWidget(self.system_page)
        self.display_stack.addWidget(self.body_page)
        self.display_stack.setCurrentIndex(0)
        self.display_stack.updateGeometry()
        self.resize(self.sizeHint())
        self.position_top_center()

        outer_layout.addWidget(self.display_stack)
        outer_layout.addWidget(self.legend_page)

        self.legend_page.hide()


    def _build_system_page(self) -> QWidget | None:
        """
        Constructs the system-summary display page.

        Creates the HUD panel and MetricWidget instances used to display
        current-system information and derived survey-summary statistics.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed system-page QWidget, or None if no initial
            system data is available.
        """   
        page, hud_layout = self.hud_factory.create_hud_page()

        title_widget = self._create_title_widget()

        hud_layout.addWidget(title_widget)
        hud_layout.addWidget(self.hud_factory.create_separator())

        if self.ui_data is None:
            return

        self.metric_system_name = MetricWidget(
            "SYSTEM",
            self.ui_data.system.system_name.upper(),
            key_label_font_color=self.hud_factory.key_label_color,
            val_label_font_color=self.hud_factory.value_label_color
        )

        self.metric_system_planet_count = MetricWidget("PLANETS", self.ui_data.summary.system_planet_count)
        self.metric_system_elw_count = MetricWidget("ELW", self.ui_data.summary.system_earthlike_world_count)
        self.metric_system_tfww_count = MetricWidget("TFWW", self.ui_data.summary.system_tf_water_world_count)
        self.metric_system_tfhmc_count = MetricWidget("TFHMC", self.ui_data.summary.system_hmc_count)
        self.metric_system_ww_count = MetricWidget("WW", self.ui_data.summary.system_water_world_count)
        self.metric_system_hmc_count = MetricWidget("HMC", self.ui_data.summary.system_hmc_count)
        self.metric_system_landable_count = MetricWidget("LANDABLE", self.ui_data.summary.system_landable_body_count)

        metrics = [
            self.metric_system_name,
            self.metric_system_planet_count,
            self.metric_system_elw_count,
            self.metric_system_tfww_count,
            self.metric_system_tfhmc_count,
            self.metric_system_ww_count,
            self.metric_system_hmc_count,
            self.metric_system_landable_count,
        ]

        self.body_display._add_metrics(hud_layout, metrics)

        return page

    def get_caspian_title_style(self) -> str:
        caspian_color = self.hud_factory.value_label_color
        return f"""
            QLabel#CaspianPanel {{
                color: {caspian_color};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 2px;
                font-family: Eurostile;
            }}
        """
    
    def get_surveyor_title_style(self) -> str:
        surveyor_color = self.hud_factory.key_label_color
        return f"""
            QLabel#SurveyorPanel {{
                color: {surveyor_color};
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
                font-family: Eurostile;
            }}
        """

    def refresh_title_label_style(self):
        for panel in self.caspian_panel:
            panel.setStyleSheet(self.get_caspian_title_style())

        for panel in self.surveyor_panel:
            panel.setStyleSheet(self.get_surveyor_title_style())


    def _create_title_widget(self) -> QWidget:
        """
        Constructs and styles the Caspian Surveyor title widget.

        Creates a vertically stacked title containing the "CASPIAN" and
        "SURVEYOR" labels with their respective stylesheet properties.

        Returns:
            The completed title QWidget.
        """    
        title_widget = QWidget()

        title_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(title_widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(6)

        app_title = QLabel("CASPIAN")
        app_title.setObjectName("CaspianPanel")
        app_title.setStyleSheet(self.get_caspian_title_style())
        self.caspian_panel.append(app_title)

        app_sub = QLabel("SURVEYOR")
        app_sub.setObjectName("SurveyorPanel")
        app_sub.setStyleSheet(self.get_surveyor_title_style())
        self.surveyor_panel.append(app_sub)
        
        layout.addWidget(app_title)
        layout.addWidget(app_sub)
        return title_widget

    def _connect_signals(self):
        """
        Connects overlay control signals to their corresponding handler methods.

        Called once during SystemInfoOverlay initialization.
        """
        self.toggle_requested.connect(self.toggle_overlay_visibility)
        self.exit_requested.connect(self.exit_overlay)

        self.cycle_next.connect(self.cycle_display_next)
        self.cycle_previous.connect(self.cycle_display_previous)
        self.cycle_default.connect(self.display_system_summary)
        self.cycle_down.connect(self.cycle_display_down)
        self.cycle_up.connect(self.cycle_display_up)
        self.toggle_legend.connect(self.toggle_physical_orbital_legend)
        self.color_picker.connect(self.toggle_color_picker)


    def _register_hotkeys(self):
        """
        Registers global keyboard hotkeys and maps each hotkey to its
        corresponding Qt signal emission.

        Called once during SystemInfoOverlay initialization.
        """
        self.hotkey_manager = HotkeyManager({
            "ctrl+shift+m": self.toggle_requested.emit,
            "ctrl+shift+e": self.exit_requested.emit,
            "ctrl+alt+right": self.cycle_next.emit,
            "ctrl+alt+left": self.cycle_previous.emit,
            "ctrl+alt+home": self.cycle_default.emit,
            "ctrl+alt+down": self.cycle_down.emit,
            "ctrl+alt+up": self.cycle_up.emit,
            "ctrl+alt+]": self.toggle_legend.emit,
            "ctrl+shift+*": self.color_picker.emit,
        })

        self.hotkey_manager.register_hotkeys()


    def _start_update_timer(self) -> None:
        """
        Starts the timer used to periodically refresh the overlay's system data.
        """

        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(
            self.refresh_system_data
        )
        self.update_timer.start(5000)

    def toggle_overlay_visibility(self) -> None:
        """
        Toggles the visibility of the Caspian Surveyor overlay.

        Hides the overlay if it is currently visible; otherwise shows it.
        """   
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def toggle_physical_orbital_legend(self) -> None:
        """
        Toggles the physical and orbital symbol legend.

        Shows the legend page while hiding the primary display stack,
        or restores the primary display stack if the legend is already visible.
        """
        if self.legend_page.isVisible():
            self.legend_page.hide()
            self.display_stack.show()

        else:
            self.display_stack.hide()
            self.legend_page.show()

    def toggle_color_picker(self) -> None:
        if self.custom_color_picker.run_config_workflow():
            self.refresh_overlay_colors()

    def refresh_overlay_colors(self) -> None:
        self.hud_factory.load_overlay_config()

        for metric in self.findChildren(MetricWidget):
            metric.set_colors(
                self.hud_factory.key_label_color,
                self.hud_factory.value_label_color
            )

        self.hud_factory.refresh_panel_colors()
        self.hud_factory.refresh_panel_glow_colors()
        self.refresh_title_label_style()
        

    def exit_overlay(self) -> None:
        """
        Exits the Caspian Surveyor overlay application.
        """

        app_instance = QApplication.instance()

        if app_instance is not None:
            app_instance.quit()
        else:
            print("Error: QApplication has not been initialized yet.")

    def cycle_display_next(self) -> None:
        if not self.planetary_bodies:
            return

        self.current_body_index = (
            self.current_body_index + 1
        ) % len(self.planetary_bodies)

        self.body_display.reset_genus_cycle()

        body = self.planetary_bodies[self.current_body_index]

        self.display_stack.setCurrentIndex(1)
        self.resize_overlay_to_current_page()

        self.body_display.update_body_display_metrics(body)

    def cycle_display_previous(self) -> None:
        """
        Cycles to the previous planetary body and displays the body page.

        Decrements the current body index with wraparound, switches the primary
        display stack to the body page, and refreshes the displayed body data.

        Does nothing if no planetary bodies are available.
        """ 
        if not self.planetary_bodies:
            return

        self.current_body_index = (
            self.current_body_index - 1
        ) % len(self.planetary_bodies)

        self.body_display.reset_genus_cycle()

        body = self.planetary_bodies[self.current_body_index]

        self.display_stack.setCurrentIndex(1)
        self.resize_overlay_to_current_page()

        self.body_display.update_body_display_metrics(body)


    def cycle_display_down(self) -> None:
        """
        Cycles to the next page in the body display stack.

        Increments the current body-page index with wraparound and displays
        the resulting page.

        Does nothing if no planetary bodies are available.
        """      
        if not self.planetary_bodies:
            return

        next_page = (
            self.body_display.display_body_stack.currentIndex() + 1
        ) % self.body_display.display_body_stack.count()

        self.body_display.display_body_stack.setCurrentIndex(next_page)
        self.body_display.display_body_stack.updateGeometry()

    def cycle_display_up(self) -> None:
        """
        Cycles to the previous page in the body display stack.

        Decrements the current body-page index with wraparound and displays
        the resulting page.

        Does nothing if no planetary bodies are available.
        """   
        if not self.planetary_bodies:
            return

        previous_page = (
            self.body_display.display_body_stack.currentIndex() - 1
        ) % self.body_display.display_body_stack.count()

        self.body_display.display_body_stack.setCurrentIndex(previous_page)
        self.body_display.display_body_stack.updateGeometry()


    def display_system_summary(self) -> None:
        """
        Changes the primary display to the system-summary page.
        """ 
        self.display_stack.setCurrentIndex(0)
        self.resize_overlay_to_current_page()


    def _create_separator(self) -> QFrame:
        """
        Creates a subtle vertical divider line between metrics.

        Returns:
            The configured separator QFrame.
        """
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("color: rgba(0, 122, 124, 25);")
        return line

    def position_top_center(self) -> None:
        """
        Positions the HUD at the top center of the primary display.

        Calculates the horizontal position using the screen and HUD widths,
        then places the overlay 15 pixels from the top of the screen.
        """
        screen_geometry = QApplication.primaryScreen().geometry()

        x = (screen_geometry.width() - self.width()) // 2
        y = -8
        self.move(x, y)

if __name__ == "__main__":
    logger.debug("Launching caspian surveyor HUD.")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    overlay = SystemInfoOverlay()
    overlay.show()
    overlay.position_top_center()
    sys.exit(app.exec())