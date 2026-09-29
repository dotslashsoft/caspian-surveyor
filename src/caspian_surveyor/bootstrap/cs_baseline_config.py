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

# file pathing
EXPLORATION_HISTORY_FILE = DATA_DIRECTORY / "exploration_history.jsonl"
CURRENT_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.json"
TEMP_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.tmp"
DATABASE_FILE = DATABASE_DIRECTORY / "caspian_surveyor.db"

#FDev specific pathing
JOURNAL_DIRECTORY = (Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous")
"""
Path to the Elite Dangerous journal directory.
"""