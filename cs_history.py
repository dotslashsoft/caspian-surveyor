import json
import bootstrap.cs_baseline_config as cs_baseline_config
import logging

logger = logging.getLogger(__name__)

EXPLORATION_HISTORY_FILE = (cs_baseline_config.run_directory / "exploration_history.jsonl")
CURRENT_SYSTEM_FILE = (cs_baseline_config.run_directory / "runtime" / "current_system.json")


class DataOrchestrator:

    def __init__(self, current_system_file=CURRENT_SYSTEM_FILE, exploration_history_file=EXPLORATION_HISTORY_FILE):
        self.current_system_file = current_system_file
        self.exploration_history_file = exploration_history_file
        self.current_system_data = None


    def load_current_system_data_to_dict(self):
        with self.current_system_file.open("r", encoding="utf-8") as file:
            self.current_system_data = json.load(file)

        return self.current_system_data


    def append_system_record_to_history_file(self):
        logger.debug("Reached append_system_record_to_history_file.")
        if self.current_system_data is None:
            logger.warning("Unable to append system history: ""no current system data loaded.")
            return False

        logger.debug("Reached actual with block to write to history file.")
        with self.exploration_history_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(self.current_system_data) + "\n")

        return True