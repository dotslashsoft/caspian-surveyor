from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemInfo:
    """
    Stores system-level data from the current system record.
    """
    system_name: str
    system_address: int
    system_position: list[float] = field(default_factory=list)
    system_body_count: int = 0

@dataclass
class SystemSummaryInfo:
    """
    Stores derived summary counts for the current system.
    """
    system_scan_record_count: int
    system_star_count: int
    system_planet_count: int
    system_belt_cluster_count: int
    system_unknown_scan_object_count: int
    system_landable_body_count: int
    system_hmc_count: int
    system_tf_hmc_count: int
    system_water_world_count: int
    system_tf_water_world_count: int
    system_earthlike_world_count: int
    system_ammonia_world_count: int

@dataclass
class SystemSignalInfo:
    """
    Represents an NSP.
    """
    system_signal_name: str
    system_signal_name_localised: str

@dataclass
class BodyMaterialInfo:
    """
    Represents a material and its percentage on a planetary body.
    """
    material_name: str
    material_percent: float

@dataclass
class BodySignalInfo:
    """
    Represents a detected planetary signal and its count.
    """
    body_signal_type: str
    body_signal_type_localised: str
    body_signal_count: int

@dataclass
class ExoBioScanInfo:
    """
    Represents an exobiology scan record for a planetary body.
    """
    exo_scan_type: str
    exo_genus: str
    exo_genus_localised: str
    exo_species: str
    exo_species_localised: str
    exo_variant: str
    exo_variant_localised: str
    exo_was_scanned_and_submitted: bool

@dataclass
class BodyGenusInfo:
    """
    Represents exobiology genus information for a planetary body.
    """
    body_genus: str
    body_genus_localised: str


@dataclass
class CelestialBody:
    """
    Represents the structured survey data for a single celestial body.

    Stores physical, orbital, scan, signal, material, and exobiology data
    loaded from the current system record.
    """
    body_id: int
    body_name: str
    body_parents: list[dict[str, int]] = field(default_factory=list)
    body_periapsis: float | None = None
    body_landable: bool = False
    body_was_discovered: bool = False
    body_was_mapped: bool = False
    body_was_footfalled: bool = False
    body_distance_from_arrival: float | None = None
    body_planet_class: str | None = None
    body_terraform_state: str | None = None
    body_materials: list[BodyMaterialInfo] | None = None
    body_surface_temperature: float | None = None
    body_atmosphere: str | None = None
    body_atmosphere_type: str | None = None
    body_radius: float | None = None
    body_surface_gravity: float | None = None
    body_surface_pressure: float | None = None
    body_semi_major_axis: float | None = None
    body_eccentricity: float | None = None
    body_orbital_inclination: float | None = None
    body_orbital_period: float | None = None
    body_ascending_node: float | None = None
    body_mean_anomaly: float | None = None
    body_rotational_period: float | None = None
    body_axial_tilt: float | None = None
    body_tidal_lock: bool = False
    body_signals: list[BodySignalInfo] | None = None
    body_dss_scan_complete: bool = False
    body_genuses: list[BodyGenusInfo] | None = None
    exobio_scans: list[ExoBioScanInfo] | None = None



    def __post_init__(self) -> None:
        """
        Converts raw material and signal dictionaries into their corresponding
        dataclass representations.

        TODO:
            Convert raw genus and organic-scan dictionaries into BodyGenusInfo and
            ExoBioScanInfo instances when exobiology data integration is completed.
        """
        if isinstance(self.body_materials, list):
            self.body_materials = [
                BodyMaterialInfo(**m) if isinstance(m, dict) else m 
                for m in self.body_materials
            ]

        # Automatically turn raw signal dictionaries into BodySignalInfo objects
        if isinstance(self.body_signals, list):
            self.body_signals = [
                BodySignalInfo(
                    body_signal_type=body_signal.get("body_signal_type", "--"),
                    body_signal_type_localised=body_signal.get("body_signal_type_localised", "--"),
                    body_signal_count=body_signal.get("body_signal_count", 0)
                )
                if isinstance(body_signal, dict)
                else body_signal
                for body_signal in self.body_signals
            ]

        if isinstance(self.body_genuses, list):
            self.body_genuses = [
                BodyGenusInfo(
                    body_genus=genus.get("body_genus", "--"),
                    body_genus_localised=genus.get("body_genus_localised", "--")
                )
                if isinstance(genus, dict)
                else genus
                for genus in self.body_genuses
            ]

        if isinstance(self.exobio_scans, list):
            self.exobio_scans = [
                ExoBioScanInfo(
                    exo_scan_type=scan.get("exo_scan_type", "--"),
                    exo_genus=scan.get("exo_genus", "--"),
                    exo_genus_localised=scan.get("exo_genus_localised", "--"),
                    exo_species=scan.get("exo_species", "--"),
                    exo_species_localised=scan.get("exo_species_localised", "--"),
                    exo_variant=scan.get("exo_variant", "--"),
                    exo_variant_localised=scan.get("exo_variant_localised", "--"),
                    exo_was_scanned_and_submitted=scan.get("exo_was_scanned_and_submitted", False)
                )
                if isinstance(scan, dict)
                else scan
                for scan in self.exobio_scans
            ]


@dataclass
class FullStarSystemPayload:
    """
    Represents the complete structured current-system payload.

    Contains system information, derived summary data, and celestial-body
    records converted from the runtime JSON structure.
    """
    schema_version: int
    system: SystemInfo
    summary: SystemSummaryInfo
    bodies: dict[str, CelestialBody] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Converts nested system, summary, and body dictionaries into their
        corresponding dataclass representations.
        """
        if isinstance(self.system, dict):
            self.system = SystemInfo(**self.system)

        if isinstance(self.summary, dict):
            self.summary = SystemSummaryInfo(**self.summary)

        if isinstance(self.bodies, dict):
            self.bodies = {
                key: (
                    CelestialBody(**value)
                    if isinstance(value, dict)
                    else value
                )
                for key, value in self.bodies.items()
            }

    @property
    def planetary_bodies(self) -> list[CelestialBody]:
        """
        Returns planetary bodies sorted by BodyID.

        Excludes bodies without a planet classification.
        """
        return sorted(
            (
                body
                for body in self.bodies.values()
                if body.body_planet_class is not None
            ),
            key=lambda body: body.body_id
        )