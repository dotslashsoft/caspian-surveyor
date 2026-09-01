import logging
import cs_journal_toolbox as Journal
from runtime import cs_runtime
### ### ### ### ### ### ### ### ### ### ### ### 
logger = logging.getLogger(__name__)

class SurveyState:

    def __init__(self):
        self.current_system = None

    
    def _get_current_system(self, event):
        current_system = self.current_system

        if current_system is None:
            return None

        event_address = event.get("SystemAddress")

        if event_address is None:
            return current_system

        if event_address != current_system["address"]:
            return None

        return current_system

    def begin_system(self, event):
        self.current_system = {
            "name": event.get("StarSystem"),
            "address": event.get("SystemAddress"),
            "position": event.get("StarPos"),
            "jump_distance": event.get("JumpDist"),
            "fuel_used": event.get("FuelUsed"),
            "fuel_level": event.get("FuelLevel"),
            "body_count": None,
            "discovery_progress": None,
            "fss_complete": False,
            "bodies": {},
        }

        logger.info("Survey state initialized for system: %s", self.current_system["name"])

    def record_discovery_scan(self, event) -> bool:
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        current_system["body_count"] = event.get("BodyCount")
        current_system["discovery_progress"] = event.get("Progress")

        return True

    def record_body_signals(self, event) -> bool:
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        body_id = event.get("BodyID")

        if body_id is None:
            logger.warning("FSSBodySignals event received without BodyID.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})

        body["BodyID"] = body_id
        body["BodyName"] = event.get("BodyName")
        body["Signals"] = event.get("Signals", [])

        return True

    def record_body_scan(self, event) -> bool:
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        body_id = event.get("BodyID")

        if body_id is None:
            logger.warning("Scan event received without BodyID.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})
        scan_type = event.get("ScanType")
        scan_types = body.setdefault("_scan_types", [])

        if scan_type and scan_type not in scan_types:
            scan_types.append(scan_type)

        body.update(event)

        return True

    def mark_all_bodies_found(self, event) -> bool:
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        already_complete = current_system["fss_complete"]

        current_system["fss_complete"] = True
        current_system["discovery_progress"] = 1.0

        if current_system["body_count"] is None:
            current_system["body_count"] = event.get("Count")

        return not already_complete

    def record_dss_complete(self, event) -> bool:
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        body_id = event.get("BodyID")

        if body_id is None:
            return False

        body = current_system["bodies"].setdefault(body_id, {})
        body["DSSScanComplete"] = True

        return True

class SurveyDataBuilder:

    def __init__(self, survey_state):
        self.survey_state = survey_state


    def build_system_record(self):
        current_system = self.survey_state.current_system

        if current_system is None:
            return None

        bodies = {}

        for body_id, body in current_system["bodies"].items():
            bodies[body_id] = self.build_body_record(body)

        return {
            "schema_version": 1,

            "system": {
                "name": current_system["name"],
                "address": current_system["address"],
                "position": current_system["position"],
                "body_count": current_system["body_count"],
            },

            "summary": self.build_system_summary(),

            "bodies": bodies,
        }

    def build_system_summary(self):
        current_system = self.survey_state.current_system
    
        if current_system is None:
            return None
    
        bodies = current_system["bodies"]
    
        summary = {
            "scan_records": len(bodies),
            "stars": 0,
            "planets": 0,
            "belt_clusters": 0,
            "unknown_scan_objects": 0,
            "landable": 0,
            "hmc": 0,
            "tf_hmc": 0,
            "water_worlds": 0,
            "tf_water_worlds": 0,
            "earthlike_worlds": 0,
            "ammonia_worlds": 0,
        }
    
        for body in bodies.values():
            if body.get("StarType"):
                summary["stars"] += 1
                continue
            
            planet_class = body.get("PlanetClass")
            if planet_class is None:
                body_name = body.get("BodyName", "")
                if "Belt Cluster" in body_name:
                    summary["belt_clusters"] += 1
                else:
                    summary["unknown_scan_objects"] += 1
                    print("UNCLASSIFIED SCAN:", body.get("BodyID"), body.get("BodyName"))
                continue
            
            summary["planets"] += 1
            if body.get("Landable"):
                summary["landable"] += 1
        
            terraformable = (body.get("TerraformState") == "Terraformable")
            if planet_class == "High metal content body":
                summary["hmc"] += 1
    
                if terraformable:
                    summary["tf_hmc"] += 1
        
            elif planet_class == "Water world":
                summary["water_worlds"] += 1
    
                if terraformable:
                    summary["tf_water_worlds"] += 1
    
            elif planet_class == "Earthlike body":
                summary["earthlike_worlds"] += 1
    
            elif planet_class == "Ammonia world":
                summary["ammonia_worlds"] += 1
    
        return summary


    def build_body_record(self, body):
        return {
            "body_id": body.get("BodyID"),
            "body_name": body.get("BodyName"),
            "parents": body.get("Parents", []),
            "planet_class": body.get("PlanetClass"),
            "terraform_state": body.get("TerraformState"),
            "materials": body.get("Materials"),
            "periapsis": body.get("Periapsis"),
            "surface_temperature": body.get("SurfaceTemperature"),
            "was_discovered": body.get("WasDiscovered", False),
            "was_mapped": body.get("WasMapped", False),
            "was_footfalled": body.get("WasFootfalled", False),
            "tidal_lock": body.get("TidalLock", False),
            "atmosphere": body.get("Atmosphere"),
            "atmosphere_type": body.get("AtmosphereType"),
            "radius": body.get("Radius"),
            "surface_gravity": body.get("SurfaceGravity"),
            "surface_pressure": body.get("SurfacePressure"),
            "semi_major_axis": body.get("SemiMajorAxis"),
            "eccentricity": body.get("Eccentricity"),
            "orbital_inclination": body.get("OrbitalInclination"),
            "orbital_period": body.get("OrbitalPeriod"),
            "ascending_node": body.get("AscendingNode"),
            "mean_anomaly": body.get("MeanAnomaly"),
            "rotational_period": body.get("RotationPeriod"),
            "axial_tilt": body.get("AxialTilt"),
            "distance_from_arrival": body.get("DistanceFromArrivalLS"),
            "signals": body.get("Signals"),
            "dss_scan_complete": body.get("DSSScanComplete", False),
            "landable": body.get("Landable", False)
        }

class StateRecovery:

    def __init__(self):
        self.survey_state = SurveyState()

    def reconstruct_system_data(self, latest_journal_events):
        if not latest_journal_events:
            return None

        oldest_matching_index = self.find_oldest_matching_journal_index(latest_journal_events)

        if oldest_matching_index is None:
            return None
        
        for journal_index in range(oldest_matching_index, -1, -1):
            journal_file = Journal.get_journal_file_by_index(journal_index)

            if journal_file is None:
                return None
            journal_events = Journal.get_latest_system_events(journal_file)

            if journal_index == oldest_matching_index:
                self.survey_state.begin_system(journal_events[0])

            self.replay_system_events(self.survey_state, journal_events[1:])

        return self.survey_state.current_system


    def replay_system_events(self, survey_state, events):

        for event in events:
            event_type = event.get("event")

            if event_type == "FSSDiscoveryScan":
                survey_state.record_discovery_scan(event)

            elif event_type == "Scan":
                survey_state.record_body_scan(event)

            elif event_type == "FSSBodySignals":
                survey_state.record_body_signals(event)

            elif event_type == "SAAScanComplete":
                survey_state.record_dss_complete(event)

            elif event_type == "FSSAllBodiesFound":
                survey_state.mark_all_bodies_found(event)

    def find_oldest_matching_journal_index(self, latest_journal_events):
        if not latest_journal_events:
            return None

        current_system_address = (latest_journal_events[0].get("SystemAddress"))

        journal_index = 1

        while True:
            journal_file = Journal.get_journal_file_by_index(journal_index)

            if journal_file is None:
                return journal_index - 1

            journal_events = Journal.get_latest_system_events(journal_file)

            previous_system_address = (journal_events[0].get("SystemAddress")
                if journal_events
                else None)

            if previous_system_address != current_system_address:
                return journal_index - 1

            journal_index += 1