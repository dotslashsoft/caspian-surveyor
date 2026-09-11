import json
import caspian_surveyor.bootstrap.cs_baseline_config as cs_baseline_config
import logging
from typing import Any

logger = logging.getLogger(__name__)

APPLICATION_DATA_DIRECTORY = cs_baseline_config.APPLICATION_DATA_DIRECTORY
RUNTIME_DIRECTORY = cs_baseline_config.RUNTIME_DIRECTORY
"""
Path: runtime directory where current_system.json lives.
"""

CURRENT_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.json"
"""
JSON formatted file that holds current system data.

Path: current_system.json file
"""

TEMP_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.tmp"
"""
JSON formatted temporary file that holds current system data.
Used temporarily to so the current system JSON file can be
atomically overwritten.

Path: current_system.tmp file
"""
##############################
def write_current_system_record(system_record: dict[str, Any] | None) -> bool:
    """
    Writes the current system record to the runtime directory.

    Writes system_record to TEMP_SYSTEM_FILE, then atomically replaces
    CURRENT_SYSTEM_FILE with the completed temporary file.

    Args:
        system_record: Current-system record produced by SurveyDataBuilder,
            or None if no current-system record is available.

    Returns:
        True if the record is written successfully; otherwise False.

    Raises:
        OSError: If writing or replacing the runtime file fails.
    """ 
    if system_record is None:
        return False

    try:
        logger.debug("Creating RUNTIME_DIRECTORY if it doesn't exist.")
        RUNTIME_DIRECTORY.mkdir(parents=True, exist_ok=True)

        logger.debug("Opening TEMP_SYSTEM_FILE and writing system record.")
        with TEMP_SYSTEM_FILE.open("w", encoding="utf-8") as file:
            json.dump(system_record, file)

        logger.debug("Attempting to overwrite CURRENT_SYSTEM_FILE with TEMP_SYSTEM_FILE.")
        TEMP_SYSTEM_FILE.replace(CURRENT_SYSTEM_FILE)

    except OSError:
        logger.exception("Unable to write current system record.")
        raise

    return True