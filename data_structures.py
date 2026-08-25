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

@dataclass
class CelestialBody:
    body_id: int
    body_name: str
    parents: List[Dict[str, int]] = field(default_factory=list)
    periapsis: float = 0.0
    was_discovered: bool = False
    was_mapped: bool = False
    was_footfalled: bool = False
    # Use Optional/Any for values that can be null or different types
    planet_class: Optional[str] = None
    terraform_state: Optional[str] = None
    surface_pressure: Optional[float] = None
    materials: Optional[List[MaterialInfo]] = None

    def __post_init__(self):
        # Automatically turn the raw materials list into MaterialInfo objects
        if isinstance(self.materials, list):
            self.materials = [
                MaterialInfo(**m) if isinstance(m, dict) else m 
                for m in self.materials
            ]

@dataclass
class FullStarSystemPayload():
    schema_version: int
    system: SystemInfo
    summary: SummaryInfo
    bodies: Dict[str, CelestialBody] = field(default_factory=dict)

    def __post_init__(self):
        # Convert nested system dict
        if isinstance(self.system, dict):
            self.system = SystemInfo(**self.system)
            
        # Convert nested summary dict
        if isinstance(self.summary, dict):
            self.summary = SummaryInfo(**self.summary)
            
        # Convert the dynamic "bodies" dictionary
        if isinstance(self.bodies, dict):
            self.bodies = {
                key: (CelestialBody(**value) if isinstance(value, dict) else value)
                for key, value in self.bodies.items()
            }


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
