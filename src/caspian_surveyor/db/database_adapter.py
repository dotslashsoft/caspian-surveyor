import sqlite3
import logging
from dataclasses import asdict
from pprint import pprint
from typing import Any
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    TESTDEV_DATABASE_FILE
)
from caspian_surveyor.db.sql_statements import (
    SYSTEM_INSERT_SQL,
    BODY_INSERT_SQL,
    BODY_PARENTS_INSERT_SQL,
    BODY_MATERIALS_INSERT_SQL,
    BODY_PHYSORB_INSERT_SQL,
    BODY_SIGNALS_INSERT_SQL,
    BODY_DETECTED_GENUSES_INSERT_SQL,
    BODY_EXOBIO_SCANS_INSERT_SQL
)

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

    def _insert_body_child_records(self, cursor, records, database_body_id, insert_sql) -> None:
        if records is None:
            return

        for record_obj in records:
            record_dict = asdict(record_obj)
            record_dict["database_body_id"] = database_body_id

            cursor.execute(insert_sql, record_dict)


    def insert_current_system_record(self, connection, full_system_data: FullStarSystemPayload):
        cursor = connection.cursor()
        try:
            with connection:
                database_system_id = self._get_existing_system_id(
                    cursor,
                    full_system_data.system.system_address
                )

                if database_system_id is None:
                    system_dict = asdict(full_system_data.system)
                    position = system_dict.pop("system_position")

                    system_dict["position_x"] = position[0]
                    system_dict["position_y"] = position[1]
                    system_dict["position_z"] = position[2]
                    cursor.execute(SYSTEM_INSERT_SQL, system_dict)
                    
                    # parent foreign key; var name == column name for simplification and readability
                    database_system_id = cursor.lastrowid

                    for body_obj in full_system_data.bodies.values():
                        body_dict = asdict(body_obj)
                        body_dict["system_id"] = database_system_id
                        cursor.execute(BODY_INSERT_SQL, body_dict)

                        database_body_id = cursor.lastrowid
                        # special-case parent relationship
                        for parent_order, parent in enumerate(body_obj.body_parents):
                            parent_dict = asdict(parent)
                            parent_dict["database_body_id"] = database_body_id
                            parent_dict["parent_order"] = parent_order
                            cursor.execute(BODY_PARENTS_INSERT_SQL, parent_dict)

                        # one-to-one physorb
                        body_dict["database_body_id"] = database_body_id
                        cursor.execute(BODY_PHYSORB_INSERT_SQL, body_dict)

                        # repeating child collections
                        self._insert_body_child_records(cursor, body_obj.body_materials, database_body_id, BODY_MATERIALS_INSERT_SQL)
                        self._insert_body_child_records(cursor, body_obj.body_signals, database_body_id, BODY_SIGNALS_INSERT_SQL)
                        self._insert_body_child_records(cursor, body_obj.body_genuses, database_body_id, BODY_DETECTED_GENUSES_INSERT_SQL)
                        self._insert_body_child_records(cursor, body_obj.exobio_scans, database_body_id, BODY_EXOBIO_SCANS_INSERT_SQL)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

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



    def query_all_systems(self, connection):
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
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_all_bodies(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT DISTINCT
                        bodies.database_body_id,
                        bodies.body_name,
                        body_materials.material_name,
                        body_materials.material_percentage
                    FROM bodies
                    JOIN body_materials
                        ON bodies.database_body_id = body_materials.database_body_id;
                    """
                )
                results = cursor.fetchall()
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_physorb_table(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT
                        CONCAT(bodies.database_body_id,': ',bodies.body_name) as full_body_id,
                        bodies.planet_class,
                        bodies.star_type,
                        body_physical_orbital_properties.radius, 
                        body_physical_orbital_properties.surface_gravity,
                        body_physical_orbital_properties.surface_pressure,
                        body_physical_orbital_properties.surface_temperature,
                        body_physical_orbital_properties.semi_major_axis,
                        body_physical_orbital_properties.eccentricity,
                        body_physical_orbital_properties.orbital_inclination,
                        body_physical_orbital_properties.orbital_period,
                        body_physical_orbital_properties.ascending_node,
                        body_physical_orbital_properties.mean_anomaly,
                        body_physical_orbital_properties.rotational_period,
                        body_physical_orbital_properties.axial_tilt,
                        body_physical_orbital_properties.periapsis
                    FROM bodies
                    INNER JOIN body_physical_orbital_properties
                        ON bodies.database_body_id = body_physical_orbital_properties.database_body_id
                    WHERE bodies.planet_class NOT LIKE '%Cluster%'
                    """
                )
                results = cursor.fetchall()
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_body_signals(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT
                        CONCAT('Body ID | ', bodies.database_body_id,': ', bodies.body_name) as full_body_id,
                        CONCAT('Signal | ', body_signals.signal_type_localised,': ', body_signals.signal_count) as signal_type_count,
                        CONCAT('-------------------------------------------------------------')
                    FROM bodies
                    INNER JOIN body_signals
                        ON bodies.database_body_id = body_signals.database_body_id
                    ORDER BY bodies.database_body_id
                    """
                )
                results = cursor.fetchall()
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_all_the_things(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT *
                    FROM systems
                    JOIN bodies
                        ON systems.database_system_id = bodies.database_system_id
                    JOIN body_parents
                        ON bodies.database_body_id = body_parents.database_body_id
                    INNER JOIN body_materials
                        ON bodies.database_body_id = body_materials.database_body_id
                    """
                )
                results = cursor.fetchall()
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_body_detected_genuses(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT
                        CONCAT('System Body: ',bodies.body_name) as system_body_name,
                        body_detected_genuses.genus_localised
                    FROM systems
                    JOIN bodies
                        ON systems.database_system_id = bodies.database_system_id
                    JOIN body_detected_genuses
                        ON bodies.database_body_id = body_detected_genuses.database_body_id
                    """
                )
                
                results = cursor.fetchall()
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def query_body_exobio_scans(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT
                        bodies.body_name,
                        body_exobio_scans.*
                    FROM bodies
                    JOIN body_exobio_scans
                        ON bodies.database_body_id = body_exobio_scans.database_body_id
                    """
                )
                
                results = cursor.fetchall()
                pprint(results)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def close_db_connection(self, connection):
        connection.close()

    def query_counts(self, connection):
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute("SELECT COUNT(*) FROM systems")
                systems_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM bodies")
                bodies_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_exobio_scans")
                exobio_count = cursor.fetchone()[0]

                print(systems_count, bodies_count, exobio_count)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise
        
        """
        SELECT COUNT(*) FROM systems;
        SELECT COUNT(*) FROM bodies;
        SELECT COUNT(*) FROM body_exobio_scans;
        """
if __name__ == "__main__":
    adapter = SqliteDataAdapter()
    conn = adapter.establish_db_connection()
    adapter.initialize_schema(conn)
    adapter.query_counts(conn)   
    adapter.close_db_connection(conn)