import json
import bootstrap.cs_baseline_config as cs_baseline_config


RUNTIME_DIRECTORY = (cs_baseline_config.run_directory / "runtime")
CURRENT_SYSTEM_FILE = (RUNTIME_DIRECTORY / "current_system.json")
TEMP_SYSTEM_FILE = (RUNTIME_DIRECTORY / "current_system.tmp")


def write_current_system_record(system_record: dict | None) -> bool:
    if system_record is None:
        return False

    RUNTIME_DIRECTORY.mkdir(parents=True, exist_ok=True)

    with TEMP_SYSTEM_FILE.open("w", encoding="utf-8") as file:
        json.dump(system_record, file)

    TEMP_SYSTEM_FILE.replace(CURRENT_SYSTEM_FILE)

    return True