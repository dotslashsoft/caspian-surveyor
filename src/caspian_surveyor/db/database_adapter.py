import sqlite3
import logging
from dataclasses import asdict
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    TESTDEV_DATABASE_FILE
)
from caspian_surveyor.db.sql_statements import *

logger = logging.getLogger(__name__)


class SqliteDataAdapter:

    def __init__(self) -> None:
        self.database_schema = DATABASE_SCHEMA
        self.database_file = TESTDEV_DATABASE_FILE

    def establish_db_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_file)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize_schema(self, connection: sqlite3.Connection) -> None:
        with self.database_schema.open("r", encoding="utf-8") as file:
            schema = file.read()
        connection.executescript(schema)

    def close_db_connection(self, connection) -> None:
        connection.close()

    def _get_existing_system_id(self, cursor, system_address) -> int | None:
        cursor.execute(
            """
            SELECT database_system_id
            FROM systems
            WHERE system_address = ?
            """,
            (system_address,)
        )

        result = cursor.fetchone()
        if result is None:
            return None
        return result[0]

    def _persist_body_child_records(self, cursor, records, database_body_id, sql_statement) -> None:
        if records is None:
            return

        for record_obj in records:
            record_dict = asdict(record_obj)
            record_dict["database_body_id"] = database_body_id

            cursor.execute(sql_statement, record_dict)

    def persist_current_system_record(self, connection, full_system_data: FullStarSystemPayload) -> None:
        cursor = connection.cursor()

        try:
            with connection:
                database_system_id = self._get_existing_system_id(
                    cursor,
                    full_system_data.system.system_address
                )

                system_dict = asdict(full_system_data.system)
                position = system_dict.pop("system_position")

                system_dict["position_x"] = position[0]
                system_dict["position_y"] = position[1]
                system_dict["position_z"] = position[2]

                if database_system_id is None:
                    cursor.execute(SYSTEM_INSERT_SQL, system_dict)
                    database_system_id = cursor.lastrowid

                else:
                    cursor.execute(SYSTEM_UPSERT_SQL, system_dict)

                for body_obj in full_system_data.bodies.values():
                    body_dict = asdict(body_obj)
                    body_dict["system_id"] = database_system_id

                    cursor.execute(BODY_UPSERT_SQL, body_dict)
                    database_body_id = cursor.fetchone()[0]
                    for parent_order, parent in enumerate(body_obj.body_parents):
                        parent_dict = asdict(parent)
                        parent_dict["database_body_id"] = database_body_id
                        parent_dict["parent_order"] = parent_order

                        cursor.execute(
                            BODY_PARENTS_UPSERT_SQL,
                            parent_dict
                        )

                    body_dict["database_body_id"] = database_body_id
                    cursor.execute(BODY_PHYSORB_UPSERT_SQL, body_dict)

                    self._persist_body_child_records(cursor, body_obj.body_materials, database_body_id, BODY_MATERIALS_UPSERT_SQL)
                    self._persist_body_child_records(cursor, body_obj.body_signals, database_body_id, BODY_SIGNALS_UPSERT_SQL)
                    self._persist_body_child_records(cursor, body_obj.body_genuses, database_body_id, BODY_DETECTED_GENUSES_UPSERT_SQL)
                    self._persist_body_child_records(cursor, body_obj.exobio_scans, database_body_id, BODY_EXOBIO_SCANS_UPSERT_SQL)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise


if __name__ == "__main__":
    # local testing only
    adapter = SqliteDataAdapter()
    conn = adapter.establish_db_connection()
    adapter.initialize_schema(conn)
    adapter.close_db_connection(conn)