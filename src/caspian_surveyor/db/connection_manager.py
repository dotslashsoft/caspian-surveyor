import sqlite3
import logging
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    DATABASE_FILE
)
logger = logging.getLogger(__name__)


class ConnectionManager:

    def __init__(self) -> None:
        self.database_schema = DATABASE_SCHEMA
        self.database_file = DATABASE_FILE


    def establish_db_connection(self) -> sqlite3.Connection:
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_file)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn


    def initialize_schema(self, connection: sqlite3.Connection) -> None:
        with self.database_schema.open("r", encoding="utf-8") as file:
            schema = file.read()
        connection.executescript(schema)


    def close_db_connection(self, connection) -> None:
        connection.close()