import json
import logging
import time
from pathlib import Path
import bootstrap.cs_log_factory as cs_log_factory
import bootstrap.cs_baseline_config as cs_baseline_config



### ### ### ### ### ### ### ### ### ### ### ### 
logger = cs_log_factory.logger
run_directory = cs_baseline_config.run_directory
journal_directory = cs_baseline_config.journal_directory



class JournalReader:

    def __init__(self, journal_path, poll_interval=1.0):
        self.journal_path = Path(journal_path)
        self.poll_interval = poll_interval

    def follow(self):
        logger.info("Beginning journal monitoring: %s", self.journal_path)
        try:
            with self.journal_path.open("r", encoding="utf-8") as journal_file:
                # Move immediately to the end of the file.
                # Only process events written after monitoring begins.
                journal_file.seek(0, 2)
                logger.debug("Journal reader positioned at end of file.")

                while True:
                    current_position = journal_file.tell()
                    line = journal_file.readline()
                    # No new journal data.
                    if not line:
                        time.sleep(self.poll_interval)
                        continue

                    # Elite may still be writing the line.
                    if not line.endswith("\n"):
                        logger.debug(
                            "Incomplete journal line encountered; "
                            "waiting for remaining data.")

                        journal_file.seek(current_position)
                        time.sleep(self.poll_interval)

                        continue

                    try:
                        event = json.loads(line)

                    except json.JSONDecodeError:
                        logger.exception(
                            "Unable to parse journal line."
                        )

                        continue

                    event_name = event.get("event", "Unknown")

                    logger.debug("Journal event received: %s", event_name)

                    if (
                        logger.isEnabledFor(logging.DEBUG)
                        and event_name in DEBUG_PAYLOAD_EVENTS
                    ):
                        logger.debug("Event payload: %s", json.dumps(event))

                    yield event

        except OSError:
            logger.exception("Unable to open or read journal file: %s", self.journal_path)
            raise

### event constants ###

EVENT_MESSAGES = {
    "FSDJump": "Entered new star system",
    "FSSDiscoveryScan": "Discovery scan completed",
    "FSSAllBodiesFound": "All system bodies discovered",
    "DockSRV": "SRV docked with ship",
    "Liftoff": "Lifted off from planetary surface",
    "SupercruiseEntry": "Entered supercruise",
    "LeaveBody": "Left planetary body",
}

EVENT_CONFIG = {
    "FSDJump": {
        "message": "Entered new star system",
        "category": "navigation",
        "important": True,
    },
    "Scan": {
        "message": "Body scan received",
        "category": "exploration",
        "important": True,
    },
    "Music": {
        "message": "Music state changed",
        "category": "game",
        "important": False,
    },
}

DEBUG_PAYLOAD_EVENTS = {
    "Location",
    "FSDJump",
    "FSSDiscoveryScan",
    "Scan",
    "FSSAllBodiesFound",
}



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

    def record_discovery_scan(self, event):
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        current_system["body_count"] = event.get("BodyCount")
        current_system["discovery_progress"] = event.get("Progress")

    def record_body_signals(self, event):
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

    def record_body_scan(self, event):
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        if not self._matches_current_system(event):
            return

        body_id = event.get("BodyID")

        if body_id is None:
            logger.warning("Scan event received without BodyID.")
            return

        body = current_system["bodies"].setdefault(body_id,{})
        scan_type = event.get("ScanType")
        scan_types = body.setdefault("_scan_types",[])

        if (scan_type and scan_type not in scan_types):
            scan_types.append(scan_type)

        body.update(event)

    def mark_all_bodies_found(self, event):
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        already_complete = current_system["fss_complete"]

        current_system["fss_complete"] = True
        current_system["discovery_progress"] = 1.0

        if current_system["body_count"] is None:
            current_system["body_count"] = event.get("Count")

        return not already_complete

    def _matches_current_system(self, event):
        if self.current_system is None:
            return False

        event_address = event.get("SystemAddress")
        if event_address is None:
            return True

        return (event_address == self.current_system["address"])

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
            "parents": body.get("Parents"),
            "planet_class": body.get("PlanetClass"),
            "terraform_state": body.get("TerraformState"),
            "materials": body.get("Materials"),
            "periapsis": body.get("Periapsis"),
            "was_discovered": body.get("WasDiscovered"),
            "was_mapped": body.get("WasMapped"),
            "was_footfalled": body.get("WasFootfalled"),
            "surface_temperature": body.get("SurfaceTemperature"),
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
            "tidal_lock": body.get("TidalLock"),
            "distance_from_arrival": body.get("DistanceFromArrivalLS"),
            "signals": body.get("Signals")
        }


def list_journal_directory_contents():
    logger.debug("Searching journal directory: %s", journal_directory)
    journal_files = list(journal_directory.glob("Journal.*.log"))
    logger.debug("Found %d journal files.", len(journal_files))

    if not journal_files:
        logger.warning("No Elite Dangerous journal files found.")
        return None
    
    latest_journal = max(journal_files, key=lambda path: path.stat().st_mtime)
    logger.info("Latest journal selected: %s", latest_journal)

    return latest_journal


EXPLORATION_HISTORY_FILE = (run_directory / "exploration_history.jsonl")
def append_system_record_to_history_file(summary):
    with EXPLORATION_HISTORY_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(summary) + "\n")


###############################################################
#                                                             #
### ###                 main process                    ### ###
#                                                             #
###############################################################

def main():
    log_manager = cs_log_factory.LogManager()
    log_manager.set_log_config()

    # display_directory_info()

    latest_journal = list_journal_directory_contents()
    if latest_journal is None:
        return

    reader = JournalReader(latest_journal, poll_interval=1.0)
    survey_state = SurveyState()
    survey_data_builder = SurveyDataBuilder(survey_state)
    print(f"Monitoring:\t\t{latest_journal}")

    try:
        for event in reader.follow():
            event_type = event.get("event")

            print(f"{event.get('timestamp')} | {event_type}")

            if event_type == "FSDJump":
                survey_state.begin_system(event)

            elif event_type == "FSSDiscoveryScan":
                survey_state.record_discovery_scan(event)

            elif event_type == "Scan":
                survey_state.record_body_scan(event)

            elif event_type == "FSSBodySignals":
                survey_state.record_body_signals(event)

            elif event_type == "FSSAllBodiesFound":
                newly_complete = (
                    survey_state.mark_all_bodies_found(event))

                if newly_complete:
                    print("FSS survey complete.")

                    survey_data_builder = SurveyDataBuilder(survey_state)
                    system_record = survey_data_builder.build_system_record()
                    append_system_record_to_history_file(system_record)

    except KeyboardInterrupt:
        print("\nJournal monitoring stopped.")

if __name__ == "__main__":
    main()