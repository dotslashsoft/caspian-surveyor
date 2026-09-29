import json
import caspian_surveyor.cs_data_structures as cs_data_structures
from caspian_surveyor.bootstrap.cs_baseline_config import (
    RUNTIME_DIRECTORY, 
    CURRENT_SYSTEM_FILE, 
    TEMP_SYSTEM_FILE
)
import logging
from dataclasses import asdict

logger = logging.getLogger(__name__)

##############################

def system_record_encoder(system_record: cs_data_structures.FullStarSystemPayload) -> dict:
    return asdict(system_record)


def system_record_decoder(raw_data: dict) -> cs_data_structures.FullStarSystemPayload:
    return cs_data_structures.FullStarSystemPayload(**raw_data)


def load_current_system_record() -> cs_data_structures.FullStarSystemPayload | None:
    """
    Loads and structures the current runtime system record.

    Reads CURRENT_SYSTEM_FILE and converts the decoded JSON data into a
    FullStarSystemPayload.

    Returns:
        The structured current-system payload, or None if the runtime file
        does not exist or contains invalid JSON.
    """
    try:
        with open(CURRENT_SYSTEM_FILE, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        return system_record_decoder(raw_data)

    except FileNotFoundError:
        logger.error("The file '%s' was not found.", CURRENT_SYSTEM_FILE)
        return None

    except json.JSONDecodeError:
        logger.error(
            "The current system file contains broken or incomplete JSON."
        )
        return None


def write_current_system_record(system_record: cs_data_structures.FullStarSystemPayload | None) -> bool:
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

    encoded_system_record = system_record_encoder(system_record)

    try:
        logger.debug("Creating RUNTIME_DIRECTORY if it doesn't exist.")
        RUNTIME_DIRECTORY.mkdir(parents=True, exist_ok=True)

        logger.debug("Opening TEMP_SYSTEM_FILE and writing system record.")
        with TEMP_SYSTEM_FILE.open("w", encoding="utf-8") as file:
            json.dump(encoded_system_record, file)

        logger.debug(
            "Attempting to overwrite CURRENT_SYSTEM_FILE with TEMP_SYSTEM_FILE."
        )
        TEMP_SYSTEM_FILE.replace(CURRENT_SYSTEM_FILE)

    except OSError:
        logger.exception("Unable to write current system record.")
        raise

    return True