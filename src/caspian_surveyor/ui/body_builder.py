import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
)
import logging
from caspian_surveyor.ui.hud_widgets import CurrentPageStackedWidget, MetricWidget

logger = logging.getLogger(__name__)




class BodyDisplayController:

    def __init__(self, hud_factory):
        self.hud_factory = hud_factory

        self.genus_dict = {}
        self.current_index = 0

        self.body_page = self._build_body_page()
        self.legend_page = self._build_legend_page()


    def _build_body_summary_page(self):
        """
        Creates the MetricWidget instances used to display
        information for the currently selected planetary body
        within a standard HUD page.

        Returns:
            The completed body-summary-page QWidget.
        """
        page, hud_layout = self.hud_factory.create_hud_page()

        self.metric_body_name = MetricWidget("PLANET", "--")
        self.metric_body_class = MetricWidget("CLASS", "--")
        self.metric_body_tf_state = MetricWidget("TF", "--")
        self.metric_body_landable = MetricWidget("LANDABLE", False)
        self.metric_body_signals = MetricWidget("SIGNALS", "--")
        self.metric_body_biosig_genus = MetricWidget("BIOSIGS", "--")
        self.metric_body_temperature = MetricWidget("TEMP K", "--")
        self.metric_body_dss_scan = MetricWidget("DSS SCAN", False)

        metrics = [
            self.metric_body_name,
            self.metric_body_class,
            self.metric_body_tf_state,
            self.metric_body_landable,
            self.metric_body_signals,
            self.metric_body_biosig_genus,
            self.metric_body_temperature,
            self.metric_body_dss_scan,
        ]

        self.body_metric_separators = self._add_metrics(hud_layout, metrics)

        return page

    def _build_body_physical_orbital_page(self):
        """
        Constructs the orbital and physical page.

        Creates MetricWidget instances within a standard HUD page to display
        a planetary body's orbital and physical properties.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed body-physical-orbital-page QWidget.
        """
        page, hud_layout = self.hud_factory.create_hud_page()

        self.metric_physorb_body_name = MetricWidget("PLANET", "--")
        self.metric_physorb_radius = MetricWidget("R⊕", "--", 12)
        self.metric_physorb_axial_tilt = MetricWidget("ε", "--", 12)
        self.metric_physorb_eccentricity = MetricWidget("e", "--", 12)
        self.metric_physorb_inclination = MetricWidget("i", "--", 12)
        self.metric_physorb_orbital_period = MetricWidget("P", "--", 12)
        self.metric_physorb_rotational_period = MetricWidget("T", "--", 12)
        self.metric_physorb_periapsis = MetricWidget("ω", "--", 12)
        self.metric_physorb_semi_major_axis = MetricWidget("a", "--", 12)

        metrics = [
            self.metric_physorb_body_name,
            self.metric_physorb_radius,
            self.metric_physorb_axial_tilt,
            self.metric_physorb_eccentricity,
            self.metric_physorb_inclination,
            self.metric_physorb_orbital_period,
            self.metric_physorb_rotational_period,
            self.metric_physorb_periapsis,
            self.metric_physorb_semi_major_axis,
        ]

        self._add_metrics(hud_layout, metrics)

        return page

    # LEGEND
    # Me:       (⌐■_■)
    # Also me:   ಥ_ಥ
    def _build_legend_page(self) -> QWidget:
        """
        Constructs the orbital and physical symbol legend page.

        Creates MetricWidget instances within a standard HUD page to define the
        symbols displayed on the body physical-orbital page.

        Called once during SystemInfoOverlay initialization.

        Returns:
            The completed body-legend QWidget.
        """
        page, hud_layout = self.hud_factory.create_hud_page()

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

        self.display_body_stack = CurrentPageStackedWidget()

        self.body_summary_page = self._build_body_summary_page()
        self.body_summary_page.updateGeometry()
        self.body_exobio_page = self._build_exobio_page()
        self.body_orbital_page = self._build_body_physical_orbital_page()

        self.display_body_stack.addWidget(self.body_summary_page)
        self.display_body_stack.addWidget(self.body_exobio_page)
        self.display_body_stack.addWidget(self.body_orbital_page)
        self.display_body_stack.setCurrentIndex(0)

        page_layout.addWidget(self.display_body_stack)

        return page

    def _build_exobio_page(self):
        """
        Constructs the exobiology display page.

        Creates the static body-name metric and retains the HUD layout so
        dynamic exobiology metrics can be added and removed at runtime.

        Returns:
            The completed exobiology-page QWidget.
        """
        page, self.exobio_hud_layout = self.hud_factory.create_hud_page()

        self.metric_exobio_body_name = MetricWidget("PLANET", "--")
        self.exobio_hud_layout.addWidget(self.metric_exobio_body_name)
        self.exobio_dynamic_widgets = []

        return page

    def _update_exobio_metrics(self, variant_statuses):
        for widget in self.exobio_dynamic_widgets:
            self.exobio_hud_layout.removeWidget(widget)
            widget.deleteLater()

        self.exobio_dynamic_widgets.clear()

        for variant_name, scan_status in variant_statuses.items():
            separator = self.hud_factory.create_separator()

            metric = MetricWidget(
                variant_name,
                "--",
                key_font_size=12,
                key_label_font_color=self.hud_factory.key_label_color,
                val_label_font_color=self.hud_factory.value_label_color
            )

            metric.set_value(scan_status)

            self.exobio_hud_layout.addWidget(separator)
            self.exobio_hud_layout.addWidget(metric)

            self.exobio_dynamic_widgets.extend([separator, metric])

    def _update_body_summary_metrics(self, body):
        self.metric_body_name.set_value(body.body_name)

        self.metric_body_class.set_value(body.planet_class)
        self.metric_body_landable.set_value(body.landable)
        #  body = self.planetary_bodies[self.current_body_index]
        if body.signals:
            signal_text = "\n".join(f"{signal.type_localised}: {signal.count}" for signal in body.signals)
            self.metric_body_signals.set_value(signal_text)
        else:
            self.metric_body_signals.set_value("--")

        self.genus_dict = {}

        if body.genuses:
            for genus in body.genuses:
                self.genus_dict[genus.genus_localised] = genus

            genus_pair = self.cycle_genus_display(self.genus_dict)
            self.metric_body_biosig_genus.set_value(genus_pair)
        else:
            self.metric_body_biosig_genus.set_value("--")

        if body.terraform_state == "Terraformable":
            self.metric_body_tf_state.setVisible(True)
            self.body_metric_separators[self.metric_body_tf_state].setVisible(True)

            self.metric_body_tf_state.set_value(body.terraform_state)

        else:
            self.metric_body_tf_state.setVisible(False)
            self.body_metric_separators[self.metric_body_tf_state].setVisible(False)

        if body.surface_temperature is not None:
            self.metric_body_temperature.set_value(f"{body.surface_temperature:.2f}")
        else:
            self.metric_body_temperature.set_value("--")
        self.metric_body_dss_scan.set_value(body.dss_scan_complete)


    def _update_body_physical_orbital_metrics(self, body):
        """
        Updates physical and orbital metrics for the selected planetary body.

        Converts stored body values into user-friendly display units and updates
        the corresponding HUD metrics.
        """
        # used for orbital body calculations
        EARTH_RADIUS_M = 6_371_000
        AU_M = 149_597_870_700
        SECONDS_PER_DAY = 86_400

        self.metric_physorb_body_name.set_value(body.body_name)
        if body.radius is not None:
            radius_earth = body.radius / EARTH_RADIUS_M
            self.metric_physorb_radius.set_value(f"{radius_earth:.3f}")
        else:
            self.metric_physorb_radius.set_value("--")

        if body.axial_tilt is not None:
            axial_tilt_degrees = math.degrees(body.axial_tilt)
            self.metric_physorb_axial_tilt.set_value(f"{axial_tilt_degrees:.2f}°")
        else:
            self.metric_physorb_axial_tilt.set_value("--")

        if body.eccentricity is not None:
            self.metric_physorb_eccentricity.set_value(f"{body.eccentricity:.6f}")
        else:
            self.metric_physorb_eccentricity.set_value("--")

        if body.orbital_inclination is not None:
            self.metric_physorb_inclination.set_value(f"{body.orbital_inclination:.2f}°")
        else:
            self.metric_physorb_inclination.set_value("--")

        if body.orbital_period is not None:
            orbital_days = body.orbital_period / SECONDS_PER_DAY
            self.metric_physorb_orbital_period.set_value(f"{orbital_days:.2f} d")
        else:
            self.metric_physorb_orbital_period.set_value("--")

        if body.rotational_period is not None:
            rotational_days = body.rotational_period / SECONDS_PER_DAY
            self.metric_physorb_rotational_period.set_value(f"{rotational_days:.2f} d")
        else:
            self.metric_physorb_rotational_period.set_value("--")

        if body.periapsis is not None:
            self.metric_physorb_periapsis.set_value(f"{body.periapsis:.2f}°")
        else:
            self.metric_physorb_periapsis.set_value("--")

        if body.semi_major_axis is not None:
            semi_major_axis_au = body.semi_major_axis / AU_M
            self.metric_physorb_semi_major_axis.set_value(f"{semi_major_axis_au:.3f} AU")
        else:
            self.metric_physorb_semi_major_axis.set_value("--")


    def _update_body_exobio_metrics(self, body):
        variant_statuses = {}
        self.metric_exobio_body_name.set_value(body.body_name)
        if body.organic_scans:
            for organic_scan in body.organic_scans:
                variant_name = organic_scan.variant_localised
                if organic_scan.scan_type == "Log":
                    scan_status = "1 Sample"
                elif organic_scan.scan_type == "Sample":
                    scan_status = "2 Samples"
                elif organic_scan.scan_type == "Analyse":
                    scan_status = "Analysed"
                else:
                    scan_status = "--"
                variant_statuses[variant_name] = scan_status

        self._update_exobio_metrics(variant_statuses)


    def update_body_display_metrics(self, body) -> None:
        """
        Updates all HUD displays for the currently selected planetary body.

        Coordinates updates for the body-summary, physical/orbital,
        and exobiology display pages.
        """
        #  body = self.planetary_bodies[self.current_body_index]
        self._update_body_summary_metrics(body)
        self._update_body_physical_orbital_metrics(body)
        self._update_body_exobio_metrics(body)

    def _add_metrics(self, layout, metrics) -> dict[MetricWidget, QFrame]:
        separators = {}

        for index, metric in enumerate(metrics):
            layout.addWidget(metric)

            if index < len(metrics) - 1:
                separator = self.hud_factory.create_separator()
                layout.addWidget(separator)

                separators[metric] = separator

        return separators

    def cycle_genus_display(self, data, step=2):
        items = list(data.keys())
        num_items = len(items)

        if self.current_index >= num_items:
            self.current_index = 0

        genus_pair_list = items[self.current_index:self.current_index + step]

        self.current_index += step

        if self.current_index >= num_items:
            self.current_index = 0

        return "\n".join(genus_pair_list)

    def reset_genus_cycle(self) -> None:
        self.current_index = 0