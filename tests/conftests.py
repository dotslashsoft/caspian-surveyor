import json
import sqlite3
import pytest
from caspian_surveyor.db.connection_manager import ConnectionManager

@pytest.fixture
def temp_db(tmp_path):
    """Provides an open, schema-initialized SQLite connection for each test."""
    db_file = tmp_path / "test_caspian.db"
    conn = sqlite3.connect(db_file)

    # Instantiate your class (passing whatever __init__ expects) and build the schema
    db_manager = ConnectionManager()
    db_manager.initialize_schema(conn)

    yield conn
    conn.close()

@pytest.fixture
def sample_journal_file(tmp_path):
    """Creates a temporary Elite Dangerous journal file with sample events."""
    journal = tmp_path / "Journal.2026-11-07T100000.01.log"
    events = [
        {"timestamp": "2026-11-07T10:00:01Z", "event": "FSDJump", "StarSystem": "Sol", "SystemAddress": 10477373803},
        {"timestamp": "2026-11-07T10:01:15Z", "event": "Scan", "BodyName": "Earth", "BodyID": 3},
    ]
    journal.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return journal