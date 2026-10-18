import json
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.bootstrap.cs_baseline_config import (
    EXPLORATION_HISTORY_FILE,
    CURRENT_SYSTEM_FILE
)
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.cs_survey_data import SurveyDataAggregator, SurveyDataBuilder
from caspian_surveyor.runtime.cs_runtime import write_current_system_record

import logging

logger = logging.getLogger(__name__)

class DataOrchestrator:
    """
    Coordinates persistence of completed system records to exploration history.

    Loads the current system record from the runtime JSON file and appends
    it to the exploration history JSONL file.
    """

    def __init__(self, current_system_file=CURRENT_SYSTEM_FILE, exploration_history_file=EXPLORATION_HISTORY_FILE):
        logger.debug("Initializing current_system_file, exploration_history_file, and current_system_data.")
        self.current_system_file = current_system_file
        self.exploration_history_file = exploration_history_file
        self.current_system_data = None


    def load_current_system_data_to_dict(self):
        """
        Loads the current system record from the runtime JSON file.

        Reads CURRENT_SYSTEM_FILE, decodes the JSON data, and returns the
        resulting current-system dictionary.

        Returns:
            Current-system data decoded from CURRENT_SYSTEM_FILE.

        Raises:
            OSError: If CURRENT_SYSTEM_FILE cannot be opened or read.
            json.JSONDecodeError: If the file contents cannot be decoded as JSON.
        """
        try:
            logger.info("Opening current_system_file...")
            with self.current_system_file.open("r", encoding="utf-8") as file:
                self.current_system_data = json.load(file)

            return self.current_system_data
        
        except OSError:
            logger.exception("Unable to load current system data.")
            raise

        except json.JSONDecodeError:
            logger.exception("Unable to decode current system data.")
            raise

    def append_system_record_to_history_file(self) -> bool:
        """
        Appends the currently loaded system record to the exploration history.

        Serializes the current-system dictionary as JSON and appends it as a
        single record to EXPLORATION_HISTORY_FILE.

        Raises:
            RuntimeError: If no current-system data is loaded.
            OSError: If the exploration-history file cannot be opened or written.

        Returns:
            True when the system record is appended successfully.
        """

        logger.debug("Reached append_system_record_to_history_file.")

        if self.current_system_data is None:
            logger.error("Unable to append system history: no current system data loaded.")
            raise RuntimeError("No current system data loaded.")

        try:
            logger.debug("Reached actual *with* block to write to history file.")
            with self.exploration_history_file.open("a", encoding="utf-8") as file:
                file.write(json.dumps(self.current_system_data) + "\n")

        except OSError:
            logger.exception("Unable to append current system data to exploration history file.")
            raise

        return True

    def get_latest_system_record_from_history(self, system_address: int) -> FullStarSystemPayload | None:

        latest_record = None

        try:
            with self.exploration_history_file.open("r", encoding="utf-8") as file:

                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Invalid exploration history record at line %d.", line_number)
                        continue

                    if not isinstance(record, dict):
                        continue

                    system = record.get("system")

                    if (isinstance(system, dict)
                        and system.get("system_address") == system_address):
                        latest_record = record

        except FileNotFoundError:
            logger.info("Exploration history file does not exist.")
            return None

        if latest_record is None:
            return None

        return FullStarSystemPayload(**latest_record)