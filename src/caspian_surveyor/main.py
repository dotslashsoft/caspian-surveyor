from pathlib import Path
import sys
from datetime import datetime
import logging
import json
import time
from pprint import pp

logger = logging.getLogger(__name__)

### ### ### ### ### ### ### ### ### ### ### ### 

run_directory = Path.cwd()

journal_directory = (
    Path.home()
    / "Saved Games"
    / "Frontier Developments"
    / "Elite Dangerous"
)


def display_directory_info():
    """Display directory information for early testing."""

    print(f"Run Directory:\t\t{run_directory}")
    print(f"Journal Directory:\t{journal_directory}")



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

class LogManager:

    DEFAULT_LOG_DIR = run_directory / "logs"
    DEFAULT_LOG_LEVEL = logging.DEBUG

    def __init__(self, log_dir=DEFAULT_LOG_DIR):
        self.log_dir = Path(log_dir)

        self.script_name = Path(sys.argv[0]).stem

        self.datetimestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.log_filename = (f"{self.script_name}_{self.datetimestamp}.log")

        self.full_log_path = (self.log_dir / self.log_filename)

        self.log_dir.mkdir(parents=True, exist_ok=True)

    def set_log_config(self):
        logging.basicConfig(
            filename=self.full_log_path,
            filemode="a",
            level=self.DEFAULT_LOG_LEVEL,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def get_log_dir(self):
        return str(self.log_dir)

    def create_log_file(self):
        self.full_log_path.touch()

        print(f"Log file created at:\t{self.full_log_path}")

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

    def build_body_record(self, body):
        return {
            ...
        }

    def build_system_summary(self, survey_state):
        current_system = survey_state.current_system
    
        if current_system is None:
            return None
    
        bodies = current_system["bodies"]
    
        summary = {
            "system_name": current_system["name"],
            "system_address": current_system["address"],
            "position": current_system["position"],
            "body_count": current_system["body_count"],
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

    def build_system_record(self):
        current_system = self.survey_state.current_system

        record = {
            "schema_version": 1,

            "system": {
                "name": current_system["name"],
                "address": current_system["address"],
                "position": current_system["position"],
            },

            "summary": self.build_system_summary(self.survey_state),

            "bodies": {},
        }

        for body_id, body in current_system["bodies"].items():
            record["bodies"][body_id] = (
                self.build_body_record(body)
            )

        return record


EXPLORATION_HISTORY_FILE = (run_directory / "exploration_history.jsonl")

def append_summary_to_history_file(summary):
    with EXPLORATION_HISTORY_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(summary) + "\n")


###############################################################
#                                                             #
### ###                 main process                    ### ###
#                                                             #
###############################################################

def main():
    log_manager = LogManager()
    log_manager.create_log_file()
    log_manager.set_log_config()

    display_directory_info()

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

            elif event_type == "FSSAllBodiesFound":
                newly_complete = (
                    survey_state.mark_all_bodies_found(event))

                if newly_complete:
                    print("FSS survey complete.")

                    summary = survey_data_builder.build_system_summary(survey_state)

                    append_summary_to_history_file(summary)
                    pp(summary)

    except KeyboardInterrupt:
        print("\nJournal monitoring stopped.")

if __name__ == "__main__":
    main()