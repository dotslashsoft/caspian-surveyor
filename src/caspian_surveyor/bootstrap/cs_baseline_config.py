from pathlib import Path
import os


APPLICATION_DATA_DIRECTORY =  Path(os.environ["LOCALAPPDATA"]) / "CaspianSurveyor"

RUNTIME_DIRECTORY = APPLICATION_DATA_DIRECTORY / "runtime"
DATA_DIRECTORY = APPLICATION_DATA_DIRECTORY / "data"
DATABASE_DIRECTORY = DATA_DIRECTORY / "db"
LOG_DIRECTORY = APPLICATION_DATA_DIRECTORY / "logs"
SIMULATION_ARCHIVES = APPLICATION_DATA_DIRECTORY / "simulation_archives"

EXPLORATION_HISTORY_FILE = DATA_DIRECTORY / "exploration_history.jsonl"
CURRENT_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.json"
TEMP_SYSTEM_FILE = RUNTIME_DIRECTORY / "current_system.tmp"
DATABASE_FILE = DATABASE_DIRECTORY / "caspian_surveyor.db"

CASPIAN_ROOT = Path(__file__).resolve().parents[1]
DATABASE_SCHEMA = CASPIAN_ROOT / "db" / "schema.sql"

HISTORICAL_EVENT_INGESTION = DATA_DIRECTORY / "historical_event_ingestion.ini"

JOURNAL_DIRECTORY = (Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous")