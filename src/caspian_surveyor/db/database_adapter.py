import sqlite3
import logging
from dataclasses import asdict
from caspian_surveyor.cs_data_structures import (
    FullStarSystemPayload,
    SystemInfo,
    SystemSummaryInfo
)
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    TESTDEV_DATABASE_FILE,
)
logger = logging.getLogger(__name__)

test_record = FullStarSystemPayload(
    schema_version=1,
    system=SystemInfo(
        system_name="Cerberous Sol",
        system_address=123456789,
        system_position=[1.0, 2.0, 3.0],
        system_body_count=16
    ),
    summary=SystemSummaryInfo(
        system_scan_record_count=0,
        system_star_count=0,
        system_planet_count=0,
        system_belt_cluster_count=0,
        system_unknown_scan_object_count=0,
        system_landable_body_count=0,
        system_hmc_count=0,
        system_tf_hmc_count=0,
        system_water_world_count=0,
        system_tf_water_world_count=0,
        system_earthlike_world_count=0,
        system_ammonia_world_count=0
    ),
    bodies={}
)

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

    def insert_current_system_record(self, connection, full_system_data: FullStarSystemPayload):
        cursor = connection.cursor()
        try:
            with connection:
                system_dict = asdict(full_system_data.system)
                position = system_dict.pop("system_position")

                system_dict["position_x"] = position[0]
                system_dict["position_y"] = position[1]
                system_dict["position_z"] = position[2]
                cursor.execute(
                    """
                    INSERT INTO systems (system_name, system_address, position_x, position_y, position_z)
                    VALUES (:system_name, :system_address, :position_x, :position_y, :position_z)
                    """, 
                    system_dict
                )

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_db(self, connection):
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT *
                    FROM systems
                    """
                )
                results = cursor.fetchall()
                print(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def close_db_connection(self, connection):
        cursor = connection.cursor()
        connection.close()


if __name__ == "__main__":
    adapter = SqliteDataAdapter()
    conn = adapter.establish_db_connection()
    adapter.initialize_schema(conn)
    adapter.query_db(conn)
    