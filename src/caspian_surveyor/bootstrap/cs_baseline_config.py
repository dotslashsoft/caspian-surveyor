from pathlib import Path
import os

APPLICATION_DATA_DIRECTORY =  Path(os.environ["LOCALAPPDATA"]) / "CaspianSurveyor"
"""
Root application-data directory for Caspian Surveyor.
"""

# directory pathing
RUNTIME_DIRECTORY = APPLICATION_DATA_DIRECTORY / "runtime"
DATA_DIRECTORY = APPLICATION_DATA_DIRECTORY / "data"
DATABASE_DIRECTORY = DATA_DIRECTORY / "db"
LOG_DIRECTORY = APPLICATION_DATA_DIRECTORY / "logs"

# mutable user data file pathing
EXPLORATION_HISTORY_FILE = DATA_DIRECTORY / "exploration_history.jsonl"
CURRENT_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.json"
TEMP_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.tmp"
DATABASE_FILE = DATABASE_DIRECTORY / "caspian_surveyor.db"
TESTDEV_DATABASE_FILE = DATABASE_DIRECTORY / "caspian_surveyor_testdev.db"

# immutable caspian file pathing
CASPIAN_ROOT = Path(__file__).resolve().parents[1]
DATABASE_SCHEMA = CASPIAN_ROOT / "db" / "schema.sql"

#FDev specific pathing
JOURNAL_DIRECTORY = (Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous")
"""
Path to the Elite Dangerous journal directory.
"""

if __name__ == "__main__":
    print(CASPIAN_ROOT)