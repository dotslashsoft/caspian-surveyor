import sys
import math
from PySide6 import QtCore
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, 
    QVBoxLayout, QFrame, QStackedWidget, QSizePolicy
)
import cs_data_structures
import keyboard
import logging

logger = logging.getLogger(__name__)

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
        key_font_size: int = 9
    ):
        """
        Initializes the MetricWidget's labels and styles.

        Args:
            key: The text title/label for the metric.
            default_value: The starting value to display. Defaults to "--".
            key_font_size: Font size in pixels for the key label. Defaults to 9.
            TODO: I wonder why I haven't implemented value_font_size
        """    
        super().__init__()

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.key_label = QLabel(key)
        self.key_label.setStyleSheet(f"""
            color: #7d8b99;
            font-family: Eurostile;
            font-size: {key_font_size}px;
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
        """
        Updates the metric value label text.

        Args:
            value: The data to display. If None, displays default "--".
        """
        self.val_label.setText(str(value))

        if value is None:
            self.val_label.setText("--")
        else:
            self.val_label.setText(str(value))


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
        """
        Initializes the overlay startup sequence.

        Connects signals, registers hotkeys, loads initial survey data,
        configures and builds the HUD, and starts the HUD update timer.
        """  
        super().__init__()

        self._connect_signals()
        self._register_hotkeys()
        self._load_initial_data()
        self._configure_window()
        self._build_ui()
        self._start_update_timer()

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

    def refresh_system_data(self):
        """
        Reloads the current system record and refreshes the HUD display.

        Updates system-summary metrics and planetary-body data from Caspian's
        current runtime record. Resets the selected body index when the system
        changes.

        This method is unaware of polling or underlying data changes. It is
        currently called every five seconds by the update timer started in
        _start_update_timer().

        TODO:
            Consider replacing timer-based polling with event-driven updates.
        """    
        ui_data = cs_data_structures.load_current_system_record()

        if ui_data is None:
            logger.debug("refresh_sysstem_data() -> ui_data is None.")
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
            self.current_body_index %= len(self.planetary_bodies)
            self.update_body_display_metrics()

        self.metric_system.set_value(ui_data.system.name.upper())
        self.metric_planets.set_value(ui_data.summary.planets)
        self.metric_elw.set_value(ui_data.summary.earthlike_worlds)
        self.metric_tfww.set_value(ui_data.summary.tf_water_worlds)
        self.metric_tfhmc.set_value(ui_data.summary.tf_hmc)
        self.metric_water_world.set_value(ui_data.summary.water_worlds)
        self.metric_hmc.set_value(ui_data.summary.hmc)
        self.metric_landable.set_value(ui_data.summary.landable)

        
    def _load_initial_data(self):
        """
        Loads the initial survey data used to populate the overlay.

        Called once during SystemInfoOverlay initialization. Loads the current
        system record, initializes the planetary-body collection, and resets
        the current body index to 0.
        """  
        self.ui_data = cs_data_structures.load_current_system_record()

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

        self.display_stack = QStackedWidget()

        self.system_page = self._build_system_page()
        self.body_page = self._build_body_page()
        self.legend_page = self._build_legend_page()

        assert self.system_page is not None
        self.display_stack.addWidget(self.system_page)
        self.display_stack.addWidget(self.body_page)
        self.display_stack.setCurrentIndex(0)

        outer_layout.addWidget(self.display_stack)
        outer_layout.addWidget(self.legend_page)

        self.legend_page.hide()


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


    def _register_hotkeys(self):
        """
        Registers global keyboard hotkeys and maps each hotkey to its
        corresponding Qt signal emission.

        Called once during SystemInfoOverlay initialization.
        """   
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

        keyboard.add_hotkey(
            "ctrl+alt+down",
            self.cycle_down.emit
        )

        keyboard.add_hotkey(
            "ctrl+alt+up",
            self.cycle_up.emit
        )

        keyboard.add_hotkey(
            "ctrl+alt+]",
            self.toggle_legend.emit
        )


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

        return page

    def _build_body_summary_page(self):
        """
        Constructs the body-summary display page.

        Creates the HUD panel and MetricWidget instances used to display
        information for the currently selected planetary body.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed body-summary-page QWidget.
        """
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
        self.metric_body_landable = MetricWidget("LANDABLE", False)
        self.metric_body_signals = MetricWidget("SIGNALS", "--")
        self.metric_body_temp = MetricWidget("TEMP K", "--")
        self.metric_body_dss = MetricWidget("DSS SCAN", False)

        metrics = [
            self.metric_body_name,
            self.metric_body_class,
            self.metric_tf_state,
            self.metric_body_landable,
            self.metric_body_signals,
            self.metric_body_temp,
            self.metric_body_dss
        ]

        self.body_metric_separators = self._add_metrics(hud_layout, metrics)

        page_layout.addWidget(panel)

        return page

    def _build_body_physical_orbital_page(self):
        """
        Constructs the body orbital-data display page.

        Creates the HUD panel and MetricWidget instances used to display
        orbital and physical information for the currently selected planetary body.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed body-orbital-page QWidget.
        """
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        self.metric_orbital_body_name = MetricWidget("PLANET", "--")
        self.metric_body_radius = MetricWidget("R⊕", "--", 12)
        self.metric_body_axial_tilt = MetricWidget("ε", "--", 12)
        self.metric_body_eccentricity = MetricWidget("e", "--", 12)
        self.metric_body_orbital_inclination = MetricWidget("i", "--", 12)
        self.metric_body_orbital_period = MetricWidget("P", "--", 12)
        self.metric_body_rotational_period = MetricWidget("T", "--", 12)
        self.metric_body_periapsis = MetricWidget("ω", "--", 12)
        self.metric_body_semi_major_axis = MetricWidget("a", "--", 12)


        metrics = [
            self.metric_orbital_body_name,
            self.metric_body_radius,
            self.metric_body_axial_tilt,
            self.metric_body_eccentricity,
            self.metric_body_orbital_inclination,
            self.metric_body_orbital_period,
            self.metric_body_rotational_period,
            self.metric_body_periapsis,
            self.metric_body_semi_major_axis,
        ]

        self._add_metrics(hud_layout, metrics)

        page_layout.addWidget(panel)

        return page

    # LEGEND
    # Me:       (⌐■_■)
    # Also me:   ಥ_ಥ
    def _build_legend_page(self) -> QWidget:
        """
        Constructs the orbital and physical symbol legend page.

        Creates the HUD panel and MetricWidget instances used to define the
        symbols displayed on the body physical-orbital page.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed body-legend QWidget.
        """
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        self.legend_body_radius = MetricWidget("R⊕", "Radius in Earth radii", 12)
        self.legend_body_axial_tilt = MetricWidget("ε", "Axial tilt / obliquity", 12)
        self.legend_body_eccentricity = MetricWidget("e", "Orbital eccentricity", 12)
        self.legend_body_orbital_inclination = MetricWidget("i", "Orbital inclination", 12)
        self.legend_body_orbital_period = MetricWidget("P", "Orbital period", 12)
        self.legend_body_rotational_period = MetricWidget("T", "Rotational period", 12)
        self.legend_body_periapsis = MetricWidget("ω", "Argument of periapsis", 12)
        self.legend_body_semi_major_axis = MetricWidget("a", "Semi-major axis", 12)

        metrics = [
            self.legend_body_radius,
            self.legend_body_axial_tilt,
            self.legend_body_eccentricity,
            self.legend_body_orbital_inclination,
            self.legend_body_orbital_period,
            self.legend_body_rotational_period,
            self.legend_body_periapsis,
            self.legend_body_semi_major_axis,
        ]

        self._add_metrics(hud_layout, metrics)
        page_layout.addWidget(panel)

        return page

    def _build_body_page(self):
        """
        Constructs the body display page.

        Creates a QStackedWidget containing the body-summary and
        body-physical-orbital pages and adds it to the body-page layout.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed body-page QWidget.
        """
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.display_body_stack = QStackedWidget()

        self.body_summary_page = self._build_body_summary_page()
        self.body_orbital_page = self._build_body_physical_orbital_page()

        self.display_body_stack.addWidget(self.body_summary_page)
        self.display_body_stack.addWidget(self.body_orbital_page)
        self.display_body_stack.setCurrentIndex(0)

        page_layout.addWidget(self.display_body_stack)

        return page

    def _build_exobio_page(self):
        """
        Builds the exobiology display page.

        TODO:
            Integrate this page into the overlay display stack and navigation
            once exobiology display functionality is implemented.

        Returns:
            The completed exobiology-page QWidget.
        """
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        panel = self._create_hud_panel()

        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        self.metric_exobio_body_name = MetricWidget("PLANET", "--")
        self.metric_exobio_signals = MetricWidget("EXOSIGNALS", "--")
        self.metric_exobio_genus = MetricWidget("GENUS", "--")
        self.metric_exobio_species = MetricWidget("SPECIES", "--")
        self.metric_exibio_variant = MetricWidget("VARIANT", "--")

        metrics = [
            self.metric_exobio_body_name,
            self.metric_exobio_signals,
            self.metric_exobio_genus,
            self.metric_exobio_species,
            self.metric_exibio_variant,
        ]

        self._add_metrics(hud_layout, metrics)
        page_layout.addWidget(panel)

        return page

    def _create_hud_panel(self):
        """
        Creates and styles a reusable HUD panel QFrame.

        Assigns the "HUDPanel" object name and applies PANEL_STYLE so the
        resulting frame can be used consistently across overlay display pages.

        Returns:
            The configured HUD-panel QFrame.
        """
        panel = QFrame()
        panel.setObjectName("HUDPanel")
        panel.setStyleSheet(self.PANEL_STYLE)
        return panel


    def _add_metrics(self, layout, metrics) -> dict[MetricWidget, QFrame]:
        """
        Adds MetricWidget instances to a HUD layout with separators between them.

        Inserts each metric into the supplied layout and creates a vertical
        separator between adjacent metrics. Returns a mapping of each metric
        to the separator immediately following it, allowing the separator to
        be referenced when the associated metric is shown or hidden.

        Args:
            layout: HUD layout receiving the metrics and separators.
            metrics: MetricWidget instances to add to the layout.

        Returns:
            A dictionary mapping each applicable MetricWidget to the QFrame
            separator immediately following it.
        """    
        separators = {}

        for index, metric in enumerate(metrics):
            layout.addWidget(metric)

            if index < len(metrics) - 1:
                separator = self._create_separator()
                layout.addWidget(separator)

                separators[metric] = separator

        return separators

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
        """
        Advances to the next planetary body and displays the body page.

        Increments the current body index with wraparound, switches the primary
        display stack to the body page, and refreshes the displayed body data.

        Does nothing if no planetary bodies are available.
        """ 
        if not self.planetary_bodies:
            return

        self.current_body_index = (
            self.current_body_index + 1
        ) % len(self.planetary_bodies)

        self.display_stack.setCurrentIndex(1)
        self.update_body_display_metrics()

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

        self.display_stack.setCurrentIndex(1)
        self.update_body_display_metrics()


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
            self.display_body_stack.currentIndex() + 1
        ) % self.display_body_stack.count()

        self.display_body_stack.setCurrentIndex(next_page)

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
            self.display_body_stack.currentIndex() - 1
        ) % self.display_body_stack.count()

        self.display_body_stack.setCurrentIndex(previous_page)


    def display_system_summary(self) -> None:
        """
        Changes the primary display to the system-summary page.
        """ 
        self.display_stack.setCurrentIndex(0)

    def update_body_display_metrics(self) -> None:
        """
        Updates the HUD metrics for the currently selected planetary body.

        Populates the body-summary and physical-orbital displays, including
        signal information, terraformability, temperature, and DSS status.

        Converts stored body data into user-friendly display units using
        EARTH_RADIUS_M, AU_M, and SECONDS_PER_DAY where applicable.
        """   

        # used for orbital body calculations
        EARTH_RADIUS_M = 6_371_000
        AU_M = 149_597_870_700
        SECONDS_PER_DAY = 86_400

        body = self.planetary_bodies[self.current_body_index]
        self.metric_body_name.set_value(body.body_name)

        # detail page
        self.metric_orbital_body_name.set_value(body.body_name)

        self.metric_body_class.set_value(body.planet_class)
        self.metric_body_landable.set_value(body.landable)

        if body.signals:
            signal_text = "\n".join(f"{signal.type_localised}: {signal.count}" for signal in body.signals)

            self.metric_body_signals.set_value(signal_text)
        else:
            self.metric_body_signals.set_value("--")

        if body.terraform_state == "Terraformable":
            self.metric_tf_state.setVisible(True)
            self.body_metric_separators[self.metric_tf_state].setVisible(True)

            self.metric_tf_state.set_value(body.terraform_state)

        else:
            self.metric_tf_state.setVisible(False)
            self.body_metric_separators[self.metric_tf_state].setVisible(False)

        if body.surface_temperature is not None:
            self.metric_body_temp.set_value(f"{body.surface_temperature:.2f}")
        else:
            self.metric_body_temp.set_value("--")
        self.metric_body_dss.set_value(body.dss_scan_complete)


        # body orbital calculations for friendly display
        if body.radius is not None:
            radius_earth = body.radius / EARTH_RADIUS_M
            self.metric_body_radius.set_value(f"{radius_earth:.3f}")
        else:
            self.metric_body_radius.set_value("--")


        if body.axial_tilt is not None:
            axial_tilt_degrees = math.degrees(body.axial_tilt)
            self.metric_body_axial_tilt.set_value(
                f"{axial_tilt_degrees:.2f}°"
            )
        else:
            self.metric_body_axial_tilt.set_value("--")


        if body.eccentricity is not None:
            self.metric_body_eccentricity.set_value(
                f"{body.eccentricity:.6f}"
            )
        else:
            self.metric_body_eccentricity.set_value("--")


        if body.orbital_inclination is not None:
            self.metric_body_orbital_inclination.set_value(
                f"{body.orbital_inclination:.2f}°"
            )
        else:
            self.metric_body_orbital_inclination.set_value("--")


        if body.orbital_period is not None:
            orbital_days = body.orbital_period / SECONDS_PER_DAY
            self.metric_body_orbital_period.set_value(
                f"{orbital_days:.2f} d"
            )
        else:
            self.metric_body_orbital_period.set_value("--")


        if body.rotational_period is not None:
            rotational_days = (
                body.rotational_period / SECONDS_PER_DAY
            )

            self.metric_body_rotational_period.set_value(
                f"{rotational_days:.2f} d"
            )
        else:
            self.metric_body_rotational_period.set_value("--")


        if body.periapsis is not None:
            self.metric_body_periapsis.set_value(
                f"{body.periapsis:.2f}°"
            )
        else:
            self.metric_body_periapsis.set_value("--")


        if body.semi_major_axis is not None:
            semi_major_axis_au = body.semi_major_axis / AU_M

            self.metric_body_semi_major_axis.set_value(
                f"{semi_major_axis_au:.3f} AU"
            )
        else:
            self.metric_body_semi_major_axis.set_value("--")


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
        y = 15
        self.move(x, y)

if __name__ == "__main__":
    logger.debug("Launching caspian surveyor HUD.")
    app = QApplication(sys.argv)
    overlay = SystemInfoOverlay()
    overlay.show()
    overlay.position_top_center()
    sys.exit(app.exec())