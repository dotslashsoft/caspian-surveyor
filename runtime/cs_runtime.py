import json
import bootstrap.cs_baseline_config as cs_baseline_config
import logging

logger = logging.getLogger(__name__)

RUNTIME_DIRECTORY = (cs_baseline_config.run_directory / "runtime")
CURRENT_SYSTEM_FILE = (RUNTIME_DIRECTORY / "current_system.json")
TEMP_SYSTEM_FILE = (RUNTIME_DIRECTORY / "current_system.tmp")


def write_current_system_record(system_record: dict | None) -> bool:
    if system_record is None:
        return False

    try:
        logger.debug("Creating RUNTIME_DIRECTORY if it doesn't exist.")
        RUNTIME_DIRECTORY.mkdir(parents=False, exist_ok=True)

        logger.debug("Opening TEMP_SYSTEM_FILE and writing system record.")
        with TEMP_SYSTEM_FILE.open("w", encoding="utf-8") as file:
            json.dump(system_record, file)

        logger.debug("Attempting to overwrite CURRENT_SYSTEM_FILE with TEMP_SYSTEM_FILE.")
        TEMP_SYSTEM_FILE.replace(CURRENT_SYSTEM_FILE)

    except OSError:
        logger.exception("Unable to write current system record.")
        raise

    return True