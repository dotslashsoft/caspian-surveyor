import sqlite3
import logging
from pprint import pprint
from caspian_surveyor.db.database_adapter import SqliteDataAdapter
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    TESTDEV_DATABASE_FILE
)
logger = logging.getLogger(__name__)
class SqliteQuery:

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

    def get_next_body_id(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT max(database_body_id) + 1 
                    FROM bodies
                    """
                )
                result = cursor.fetchone()
                pprint(result)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

    def get_most_recent_body(self, connection) -> None:
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute(
                    """
                    SELECT max(database_body_id)
                    FROM bodies
                    """
                )
                result = cursor.fetchone()
                pprint(result)

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

    def persistence_query_testing(self, connection):
        cursor = connection.cursor()
        try:
            with connection:
                cursor.execute("SELECT COUNT(*) FROM systems;")
                systems_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM bodies;")
                bodies_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_parents;")
                parents_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_materials;")
                materials_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_physical_orbital_properties;")
                physorb_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_signals;")
                signals_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_detected_genuses;")
                genuses_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM body_exobio_scans;")
                exobio_count = cursor.fetchone()[0]

                print(systems_count, bodies_count, parents_count, materials_count, physorb_count, signals_count, genuses_count, exobio_count)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise
        
        
        
        
        


if __name__ == '__main__':
    adapter = SqliteDataAdapter()
    query = SqliteQuery()
    conn = adapter.establish_db_connection()
    adapter.initialize_schema(conn)
    query.persistence_query_testing(conn)
    adapter.close_db_connection(conn)