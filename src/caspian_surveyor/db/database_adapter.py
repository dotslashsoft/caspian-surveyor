import sqlite3
import logging
from dataclasses import asdict
from pprint import pprint
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    TESTDEV_DATABASE_FILE
)
logger = logging.getLogger(__name__)

SYSTEM_INSERT_SQL = \
"""
INSERT INTO systems (
    system_name,
    system_address,
    system_body_count,
    position_x,
    position_y,
    position_z
)
VALUES (
    :system_name,
    :system_address,
    :system_body_count,
    :position_x,
    :position_y,
    :position_z
)
"""

BODY_INSERT_SQL = \
"""
INSERT INTO bodies (
    database_system_id,
    elite_body_id,
    body_name,
    planet_class,
    star_type,
    terraform_state,
    was_discovered,
    was_mapped,
    was_footfalled,
    landable,
    dss_scan_complete,
    tidal_lock,
    atmosphere,
    atmosphere_type,
    distance_from_arrival
)
VALUES (
    :system_id,
    :body_id,
    :body_name,
    :body_planet_class,
    :body_star_type,
    :body_terraform_state,
    :body_was_discovered,
    :body_was_mapped,
    :body_was_footfalled,
    :body_landable,
    :body_dss_scan_complete,
    :body_tidal_lock,
    :body_atmosphere,
    :body_atmosphere_type,
    :body_distance_from_arrival
)
"""

BODY_PARENTS_INSERT_SQL = \
"""
INSERT INTO body_parents (
    database_body_id,
    parent_order,
    parent_elite_body_id,
    parent_type
)
VALUES (
    :database_body_id,
    :parent_order,
    :parent_body_id,
    :parent_type
)
"""

BODY_MATERIALS_INSERT_SQL = \
"""
INSERT INTO body_materials (
    database_body_id,
    material_name,
    material_percentage
)
VALUES (
    :database_body_id,
    :material_name,
    :material_percent
)
"""

BODY_PHYSORB_INSERT_SQL = \
"""
INSERT INTO body_physical_orbital_properties (
    database_body_id,
    radius,
    surface_gravity,
    surface_pressure,
    surface_temperature,
    semi_major_axis,
    eccentricity,
    orbital_inclination,
    orbital_period,
    ascending_node,
    mean_anomaly,
    rotational_period,
    axial_tilt,
    periapsis
)
VALUES (
    :database_body_id,
    :body_radius,
    :body_surface_gravity,
    :body_surface_pressure,
    :body_surface_temperature,
    :body_semi_major_axis,
    :body_eccentricity,
    :body_orbital_inclination,
    :body_orbital_period,
    :body_ascending_node,
    :body_mean_anomaly,
    :body_rotational_period,
    :body_axial_tilt,
    :body_periapsis
)
"""


BODY_SIGNALS_INSERT_SQL = \
"""
INSERT INTO body_signals (
    database_body_id,
    signal_type,
    signal_type_localised,
    signal_count
)
VALUES (
    :database_body_id,
    :body_signal_type,
    :body_signal_type_localised,
    :body_signal_count
)
"""



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
                cursor.execute(SYSTEM_INSERT_SQL, system_dict)
                
                # parent foreign key; var name == column name for simplification and readability
                database_system_id = cursor.lastrowid

                for body_obj in full_system_data.bodies.values():
                    body_dict = asdict(body_obj)
                    body_dict["system_id"] = database_system_id

                    cursor.execute(BODY_INSERT_SQL, body_dict)

                    database_body_id = cursor.lastrowid
                    
                    for parent_order, parent in enumerate(body_obj.body_parents):
                        parent_dict = asdict(parent)

                        parent_dict["database_body_id"] = database_body_id
                        parent_dict["parent_order"] = parent_order

                        cursor.execute(BODY_PARENTS_INSERT_SQL, parent_dict)

                    if body_obj.body_materials is not None:
                        for material_obj in body_obj.body_materials:
                            material_dict = asdict(material_obj)
                            material_dict["database_body_id"] = database_body_id

                            cursor.execute(BODY_MATERIALS_INSERT_SQL, material_dict)

                    body_dict["database_body_id"] = database_body_id
                    cursor.execute(BODY_PHYSORB_INSERT_SQL, body_dict)

                    if body_obj.body_signals is not None:
                        for body_signal_obj in body_obj.body_signals:
                            body_signal_dict = asdict(body_signal_obj)
                            body_signal_dict["database_body_id"] = database_body_id

                            cursor.execute(BODY_SIGNALS_INSERT_SQL, body_signal_dict)

        except sqlite3.Error as e:
            print(f"Transaction failed! Database changes rolled back automatically: {e}")
            raise

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

    def close_db_connection(self, connection):
        connection.close()


if __name__ == "__main__":
    adapter = SqliteDataAdapter()
    conn = adapter.establish_db_connection()
    adapter.initialize_schema(conn)
    adapter.query_body_signals(conn)
    adapter.close_db_connection(conn)