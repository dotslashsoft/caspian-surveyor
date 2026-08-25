from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import main

exploration_history_jsonl = main.EXPLORATION_HISTORY_FILE

@dataclass
class SystemInfo:
    name: str
    address: int
    position: List[float] = field(default_factory=list)
    body_count: int = 0

@dataclass
class SummaryInfo:
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
    Name: str
    Percent: float

# {
#   "timestamp": "2026-08-25T18:43:19Z",
#   "event": "FSSBodySignals",
#   "BodyName": "Blaea Thio NU-X c14-11 8 c",
#   "BodyID": 54,
#   "SystemAddress": 3062412350594,
#   "Signals": [
#     {
#       "Type": "$SAA_SignalType_Biological;",
#       "Type_Localised": "Biological",
#       "Count": 4
#     }
#   ]
# }

@dataclass
class SignalInfo:
    type: str
    type_localised: str
    count: int

@dataclass
class CelestialBody:
    body_id: int
    body_name: str
    parents: List[Dict[str, int]] = field(default_factory=list)
    periapsis: Optional[float] = None
    was_discovered: bool = False
    was_mapped: bool = False
    was_footfalled: bool = False
    distance_from_arrival: Optional[float] = None
    # Use Optional/Any for values that can be null or different types
    planet_class: Optional[str] = None
    terraform_state: Optional[str] = None
    materials: Optional[List[MaterialInfo]] = None
    surface_temperature: Optional[float] = None
    atmosphere: Optional[str] = None
    atmosphere_type: Optional[str] = None
    radius: Optional[float] = None
    surface_gravity: Optional[float] = None
    surface_pressure: Optional[float] = None
    semi_major_axis: Optional[float] = None
    eccentricity: Optional[float] = None
    orbital_inclination: Optional[float] = None
    orbital_period: Optional[float] = None
    ascending_node: Optional[float] = None
    mean_anomaly: Optional[float] = None
    rotational_period: Optional[float] = None
    axial_tilt: Optional[float] = None
    tidal_lock: bool = False
    signals: Optional[List[SignalInfo]] = None

    


    def __post_init__(self):
        # Automatically turn the raw materials list into MaterialInfo objects
        if isinstance(self.materials, list):
            self.materials = [
                MaterialInfo(**m) if isinstance(m, dict) else m 
                for m in self.materials
            ]

        # Automatically turn raw signal dictionaries into SignalInfo objects
        if isinstance(self.signals, list):
            self.signals = [
                SignalInfo(
                    type=signal.get("Type"),
                    type_localised=signal.get("Type_Localised"),
                    count=signal.get("Count")
                )
                if isinstance(signal, dict)
                else signal
                for signal in self.signals
            ]


@dataclass
class FullStarSystemPayload():
    schema_version: int
    system: SystemInfo
    summary: SummaryInfo
    bodies: Dict[str, CelestialBody] = field(default_factory=dict)

    def __post_init__(self):
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
        return sorted(
            (
                body
                for body in self.bodies.values()
                if body.planet_class is not None
            ),
            key=lambda body: body.body_id
        )




def load_latest_system_record():
    try:
        with open(exploration_history_jsonl, "r", encoding="utf-8") as file:
            lines = file.readlines()

            if not lines:
                print("The file is empty.")
                return None

            last_line = lines[-1].strip()

            if not last_line and len(lines) > 1:
                last_line = lines[-2].strip()

            if not last_line:
                print("The file appears to be empty.")
                return None

            raw_data = json.loads(last_line)
            system_record = FullStarSystemPayload(**raw_data)

            return system_record

    except FileNotFoundError:
        print(f"Error: The file '{exploration_history_jsonl}' was not found.")
        return None

    except json.JSONDecodeError:
        print("Error: The last line of the file is broken or incomplete JSON.")
        return None




if __name__ == "__main__":
    latest_payload = load_latest_system_record()

    if latest_payload is not None:
        print("Successfully loaded the most recent entry!")
