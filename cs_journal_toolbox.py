import json
import logging
import time
import bootstrap.cs_log_factory as cs_log_factory
import bootstrap.cs_baseline_config as cs_baseline_config
from pathlib import Path
import runtime.cs_runtime as cs_runtime

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
        

def get_latest_journal_file():
    logger.debug("Searching journal directory: %s", journal_directory)
    journal_files = list(journal_directory.glob("Journal.*.log"))
    logger.debug("Found %d journal files.", len(journal_files))

    if not journal_files:
        logger.warning("No Elite Dangerous journal files found.")
        return None
    
    latest_journal = max(journal_files, key=lambda path: path.stat().st_mtime)
    logger.info("Latest journal selected: %s", latest_journal)

    return latest_journal


def get_latest_system_events(journal_file: Path) -> list[dict]:
    latest_system_events = []

    with journal_file.open("r", encoding="utf-8") as file:
        for line in file:
            event = json.loads(line)

            event_type = event.get("event")

            if event_type in {"FSDJump", "Location"}:
                latest_system_events = [event]

            elif latest_system_events:
                latest_system_events.append(event)

    return latest_system_events

def get_journal_file_by_index(index):
    logger.debug("Searching journal directory for file index %d: %s", index, journal_directory)

    journal_files = list(journal_directory.glob("Journal.*.log"))
    logger.debug("Found %d journal files.", len(journal_files))

    if index >= len(journal_files):
        return None

    journal_files.sort(key=lambda path: path.stat().st_mtime,reverse=True)
    journal_file = journal_files[index]

    logger.info("Journal file selected at index %d: %s", index, journal_file)

    return journal_file


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
    "SAAScanComplete"
}

if __name__ == "__main__":
    pass