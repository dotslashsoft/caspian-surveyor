from dataclasses import dataclass, field
import json
import logging
import runtime.cs_runtime as cs_runtime


logger = logging.getLogger(__name__)
CURRENT_SYSTEM_FILE = cs_runtime.CURRENT_SYSTEM_FILE


@dataclass
class SystemInfo:
    """
    Stores system-level data from the current system record.
    """
    name: str
    address: int
    position: list[float] = field(default_factory=list)
    body_count: int = 0

@dataclass
class SummaryInfo:
    """
    Stores derived summary counts for the current system.
    """
    scan_records: int
    stars: int
    planets: int
    belt_clusters: int
    unknown_scan_objects: int
    landable: int
    hmc: int
    tf_hmc: int
    water_worlds: int
    tf_water_worlds: int
    earthlike_worlds: int
    ammonia_worlds: int

@dataclass
class MaterialInfo:
    """
    Represents a material and its percentage on a planetary body.
    """
    Name: str
    Percent: float

@dataclass
class SignalInfo:
    """
    Represents a detected planetary signal and its count.
    """
    type: str
    type_localised: str
    count: int

@dataclass
class OrganicScanInfo:
    """
    Represents an exobiology scan record for a planetary body.
    """
    scan_type: str
    genus: str
    genus_localised: str
    species: str
    species_localised: str
    variant: str
    variant_localised: str
    was_scanned_and_submitted: bool

@dataclass
class GenusInfo:
    """
    Represents exobiology genus information for a planetary body.
    """
    genus: str
    genus_localised: str


@dataclass
class CelestialBody:
    """
    Represents the structured survey data for a single celestial body.

    Stores physical, orbital, scan, signal, material, and exobiology data
    loaded from the current system record.
    """
    body_id: int
    body_name: str
    parents: list[dict[str, int]] = field(default_factory=list)
    periapsis: float | None = None
    landable: bool = False
    was_discovered: bool = False
    was_mapped: bool = False
    was_footfalled: bool = False
    distance_from_arrival: float | None = None
    planet_class: str | None = None
    terraform_state: str | None = None
    materials: list[MaterialInfo] | None = None
    surface_temperature: float | None = None
    atmosphere: str | None = None
    atmosphere_type: str | None = None
    radius: float | None = None
    surface_gravity: float | None = None
    surface_pressure: float | None = None
    semi_major_axis: float | None = None
    eccentricity: float | None = None
    orbital_inclination: float | None = None
    orbital_period: float | None = None
    ascending_node: float | None = None
    mean_anomaly: float | None = None
    rotational_period: float | None = None
    axial_tilt: float | None = None
    tidal_lock: bool = False
    signals: list[SignalInfo] | None = None
    dss_scan_complete: bool = False
    genuses: list[GenusInfo] | None = None
    organic_scans: list[OrganicScanInfo] | None = None
    


    def __post_init__(self) -> None:
        """
        Converts raw material and signal dictionaries into their corresponding
        dataclass representations.

        TODO:
            Convert raw genus and organic-scan dictionaries into GenusInfo and
            OrganicScanInfo instances when exobiology data integration is completed.
        """
        if isinstance(self.materials, list):
            self.materials = [
                MaterialInfo(**m) if isinstance(m, dict) else m 
                for m in self.materials
            ]

        # Automatically turn raw signal dictionaries into SignalInfo objects
        if isinstance(self.signals, list):
            self.signals = [
                SignalInfo(
                    type=signal.get("Type", "--"),
                    type_localised=signal.get("Type_Localised", "--"),
                    count=signal.get("Count", 0)
                )
                if isinstance(signal, dict)
                else signal
                for signal in self.signals
            ]

        if isinstance(self.genuses, list):
            self.genuses = [
                GenusInfo(
                    genus=genus.get("Genus", "--"),
                    genus_localised=genus.get("Genus_Localised", "--")
                )
                if isinstance(genus, dict)
                else genus
                for genus in self.genuses
            ]

        if isinstance(self.organic_scans, list):
            self.organic_scans = [
                OrganicScanInfo(
                    scan_type=scan.get("ScanType", "--"),
                    genus=scan.get("Genus", "--"),
                    genus_localised=scan.get("Genus_Localised", "--"),
                    species=scan.get("Species", "--"),
                    species_localised=scan.get("Species_Localised", "--"),
                    variant=scan.get("Variant", "--"),
                    variant_localised=scan.get("Variant_Localised", "--"),
                    was_scanned_and_submitted=scan.get("WasLogged", False)
                )
                if isinstance(scan, dict)
                else scan
                for scan in self.organic_scans
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
    summary: SummaryInfo
    bodies: dict[str, CelestialBody] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Converts nested system, summary, and body dictionaries into their
        corresponding dataclass representations.
        """
        if isinstance(self.system, dict):
            self.system = SystemInfo(**self.system)

        if isinstance(self.summary, dict):
            self.summary = SummaryInfo(**self.summary)

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
                if body.planet_class is not None
            ),
            key=lambda body: body.body_id
        )


def load_current_system_record() -> FullStarSystemPayload | None:
    """
    Loads and structures the current runtime system record.

    Reads CURRENT_SYSTEM_FILE and converts the decoded JSON data into a
    FullStarSystemPayload.

    Returns:
        The structured current-system payload, or None if the runtime file
        does not exist or contains invalid JSON.
    """
    try:
        with open(CURRENT_SYSTEM_FILE, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        system_record = FullStarSystemPayload(**raw_data)

        return system_record

    except FileNotFoundError:
        logger.error("The file '%s' was not found.", CURRENT_SYSTEM_FILE)
        return None

    except json.JSONDecodeError:
        logger.error("The current system file contains broken or incomplete JSON.")
        return None