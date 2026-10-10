import sqlite3
import logging
from pprint import pprint
from dataclasses import asdict
import json
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    TESTDEV_DATABASE_FILE
)
from caspian_surveyor.cs_data_structures import (
    FullStarSystemPayload,
    CelestialBody,
    SystemInfo,
    BodyParentInfo,
    BodyMaterialInfo,
    BodySignalInfo,
    BodyGenusInfo,
    ExoBioScanInfo,
    SystemSummaryInfo
)
from caspian_surveyor.runtime.cs_runtime import load_current_system_record
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


class ArchivedSystemQueries:
    """
    Class containing methods to retrieve previously archived Caspian system state.
    """

    def __init__(self) -> None:
        self.database_schema = DATABASE_SCHEMA
        self.database_file = TESTDEV_DATABASE_FILE

    # --- begin connection methods
    def establish_db_connection(self) -> sqlite3.Connection:
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
    # --- end connection methods

    def get_system_id(self, cursor: sqlite3.Cursor, system_address: int) -> int | None:
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

    def _query_system_body_counts(self, connection: sqlite3.Connection, database_system_id: int) -> sqlite3.Row | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS total_bodies,
            SUM(
                CASE
                    WHEN star_type IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS star_count,

            SUM(
                CASE
                    WHEN planet_class IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS planet_count
            FROM bodies
            WHERE database_system_id = ?;
            """,
            (database_system_id,)
        )

        results = cursor.fetchone()

        return results

    def _construct_archived_system(self, system_row: sqlite3.Row) -> SystemInfo:
        return SystemInfo(
            system_name=system_row["system_name"],
            system_address=system_row["system_address"],
            system_position=[
                system_row["position_x"],
                system_row["position_y"],
                system_row["position_z"]
            ],
            system_body_count=system_row["system_body_count"],
        )
    
    def _construct_archived_bodies(self, bodies):
        bodies.sort(key=lambda body: body["database_body_id"])
        bodies_by_database_id = {}
        bodies_by_elite_id = {}

        for body_obj in bodies:
            body_obj_dict = {
                "body_id": body_obj[2],
                "body_name": body_obj[3],
                "body_planet_class": body_obj[4],
                "body_star_type": body_obj[5],
                "body_terraform_state": body_obj[6],
                "body_was_discovered": body_obj[7],
                "body_was_mapped": body_obj[8],
                "body_was_footfalled": body_obj[9],
                "body_landable": body_obj[10],
                "body_dss_scan_complete": body_obj[11],
                "body_tidal_lock": body_obj[12],
                "body_atmosphere": body_obj[13],
                "body_atmosphere_type": body_obj[14],
                "body_distance_from_arrival": body_obj[15],
            }

            celestial_body = CelestialBody(
                **body_obj_dict
            )

            database_body_id = body_obj[0]
            body_id = body_obj[2]

            bodies_by_database_id[database_body_id] = celestial_body
            bodies_by_elite_id[body_id] = celestial_body

        return bodies_by_database_id, bodies_by_elite_id

    def _construct_archived_body_parents(self, parents, bodies_by_database_id):
        parents.sort(key=lambda parent: (parent[0], parent[1]))
        for parent in parents:
            database_body_id = parent[0]

            parent_obj = BodyParentInfo(parent_type=parent[3], parent_body_id=parent[2])

            bodies_by_database_id[database_body_id].body_parents.append(parent_obj)

    def _construct_archived_body_materials(self, materials, bodies_by_database_id):
        materials.sort(key=lambda material: material[0])
        for material in materials:
            database_body_id = material[0]

            material_obj = BodyMaterialInfo(material_name=material[1], material_percent=material[2])

            body = bodies_by_database_id[database_body_id]

            if body.body_materials is None:
                body.body_materials = []

            body.body_materials.append(material_obj)

    def _construct_archived_body_physorb(self, body_physorb, bodies_by_database_id):

        body_physorb.sort(key=lambda physorb: physorb[0])
        for physorb in body_physorb:
            database_body_id = physorb[0]
            physorb_obj_dict = {
                "body_radius": physorb[1],
                "body_surface_gravity": physorb[2],
                "body_surface_pressure": physorb[3],
                "body_surface_temperature": physorb[4],
                "body_semi_major_axis": physorb[5],
                "body_eccentricity": physorb[6],
                "body_orbital_inclination": physorb[7],
                "body_orbital_period": physorb[8],
                "body_ascending_node": physorb[9],
                "body_mean_anomaly": physorb[10],
                "body_rotational_period": physorb[11],
                "body_axial_tilt": physorb[12],
                "body_periapsis": physorb[13]
            }

            body = bodies_by_database_id[database_body_id]

            for field_name, value in physorb_obj_dict.items():
                setattr(body, field_name, value)

    def _construct_archived_body_signals(self, signals, bodies_by_database_id):
        signals.sort(key=lambda signal: signal[0])
        for signal in signals:
            database_body_id = signal[0]

            signal_obj = BodySignalInfo(body_signal_type=signal[1], body_signal_type_localised=signal[2], body_signal_count=signal[3])

            body = bodies_by_database_id[database_body_id]

            if body.body_signals is None:
                body.body_signals = []

            body.body_signals.append(signal_obj)

    def _construct_archived_body_genuses(self, genuses, bodies_by_database_id):
        genuses.sort(key=lambda genus: genus[0])
        for genus in genuses:
            database_body_id = genus[0]

            genus_obj = BodyGenusInfo(body_genus=genus[1], body_genus_localised=genus[2])

            body = bodies_by_database_id[database_body_id]

            if body.body_genuses is None:
                body.body_genuses = []

            body.body_genuses.append(genus_obj)

    def _construct_archived_body_exobio(self, exobio_scans, bodies_by_database_id):
        exobio_scans.sort(key=lambda exobio: exobio[1])
        for exobio in exobio_scans:
            database_body_id = exobio[1]

            exobio_obj = ExoBioScanInfo(
                exo_scan_timestamp=exobio[3],
                exo_scan_type=exobio[2],
                exo_genus=exobio[4],
                exo_genus_localised=exobio[5],
                exo_species=exobio[6],
                exo_species_localised=exobio[7],
                exo_variant=exobio[8],
                exo_variant_localised=exobio[9],
                exo_was_logged=exobio[10]
            )

            body = bodies_by_database_id[database_body_id]

            if body.exobio_scans is None:
                body.exobio_scans = []


            body.exobio_scans.append(exobio_obj)

    def _construct_system_summary_info(self, bodies_by_elite_id) -> SystemSummaryInfo:
        system_summary = SystemSummaryInfo(
            system_scan_record_count=len(bodies_by_elite_id),
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
            system_ammonia_world_count=0,
        )


        for body in bodies_by_elite_id.values():
            if body.body_materials:
                body.body_materials.sort(
                    key=lambda material: material.material_percent,
                    reverse=True
                )

            if body.body_star_type:
                system_summary.system_star_count += 1
                continue

            planet_class = body.body_planet_class
            if planet_class is None:
                body_name = body.body_name
                if "Belt Cluster" in body_name:
                    system_summary.system_belt_cluster_count += 1
                else:
                    system_summary.system_unknown_scan_object_count += 1
                continue

            system_summary.system_planet_count += 1
            if body.body_landable:
                system_summary.system_landable_body_count += 1

            terraformable = (body.body_terraform_state == "Terraformable")
            if planet_class == "High metal content body":
                system_summary.system_hmc_count += 1
                if terraformable:
                    system_summary.system_tf_hmc_count += 1

            elif planet_class == "Water world":
                system_summary.system_water_world_count += 1
                if terraformable:
                    system_summary.system_tf_water_world_count += 1

            elif planet_class == "Earthlike body":
                system_summary.system_earthlike_world_count += 1

            elif planet_class == "Ammonia world":
                system_summary.system_ammonia_world_count += 1

        return system_summary

    # --- begin archived system queries
    def get_archived_system_info(self, connection: sqlite3.Connection, system_address: int):
        cursor = connection.cursor()

        database_system_id = self.get_system_id(
            cursor,
            system_address
        )
        if database_system_id is None:
            return None

        system = self._get_system_info(cursor, database_system_id)
        bodies = self._get_system_bodies(cursor, database_system_id)
        parents = self._get_system_parents(cursor, database_system_id)
        materials = self._get_system_materials(cursor, database_system_id)
        physorb = self._get_system_physorb(cursor, database_system_id)
        signals = self._get_system_signals(cursor, database_system_id)
        genuses = self._get_system_genuses(cursor, database_system_id)
        exobio = self._get_system_exobio(cursor, database_system_id)

        system_info = self._construct_archived_system(system)
        bodies_by_database_id, bodies_by_elite_id = (
            self._construct_archived_bodies(bodies)
        )
        body_parents_info = self._construct_archived_body_parents(parents, bodies_by_database_id)
        body_materials_info = self._construct_archived_body_materials(materials, bodies_by_database_id)
        body_physorb_info = self._construct_archived_body_physorb(physorb, bodies_by_database_id)
        body_signal_info = self._construct_archived_body_signals(signals, bodies_by_database_id)
        body_genus_info = self._construct_archived_body_genuses(genuses, bodies_by_database_id)
        body_exobio_info = self._construct_archived_body_exobio(exobio, bodies_by_database_id)

        system_summary_body_counts = self._query_system_body_counts(connection, database_system_id)

        # print(system_body_counts["total_bodies"])
        # print(system_body_counts["star_count"])
        # print(system_body_counts["planet_count"])

        system_summary_info = self._construct_system_summary_info(bodies_by_elite_id)

        # pprint(system_summary_info)
        for body in bodies_by_database_id.values():
            if body.exobio_scans:
                body.exobio_scans.sort(
                    key=lambda scan: scan.exo_scan_timestamp
                )

        return FullStarSystemPayload(
            schema_version=1,
            system=system_info,
            summary=system_summary_info,
            bodies=bodies_by_elite_id
        )


    def _compare_fullstarsystem_payloads(self, original: FullStarSystemPayload, reconstructed: FullStarSystemPayload):
        original_normalized = json.loads(json.dumps(asdict(original)))
        reconstructed_normalized = json.loads(json.dumps(asdict(reconstructed)))

        for payload in (original_normalized, reconstructed_normalized):
            for body in payload["bodies"].values():
                for field in ("body_signals", "body_genuses"):
                    if body[field] is not None:
                        body[field].sort(key=lambda record: json.dumps(record, sort_keys=True))

        if original_normalized != reconstructed_normalized:
            raise AssertionError(
                "FullStarSystemPayload round-trip validation failed."
            )


    def _get_system_info(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT *
            FROM systems
            WHERE database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchone()


    def _get_system_bodies(self, cursor: sqlite3.Cursor, database_system_id: int) -> list[tuple]:
        cursor.execute(
            """
            SELECT *
            FROM bodies
            WHERE database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


    def _get_system_parents(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT body_parents.*
            FROM body_parents
            JOIN bodies 
                ON body_parents.database_body_id = bodies.database_body_id
            WHERE bodies.database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


    def _get_system_materials(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT body_materials.*
            FROM body_materials
            JOIN bodies 
                ON body_materials.database_body_id = bodies.database_body_id
            WHERE bodies.database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


    def _get_system_physorb(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT body_physical_orbital_properties.*
            FROM body_physical_orbital_properties
            JOIN bodies 
                ON body_physical_orbital_properties.database_body_id = bodies.database_body_id
            WHERE bodies.database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


    def _get_system_signals(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT body_signals.*
            FROM body_signals
            JOIN bodies 
                ON body_signals.database_body_id = bodies.database_body_id
            WHERE bodies.database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


    def _get_system_genuses(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT body_detected_genuses.*
            FROM body_detected_genuses
            JOIN bodies 
                ON body_detected_genuses.database_body_id = bodies.database_body_id
            WHERE bodies.database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


    def _get_system_exobio(self, cursor, database_system_id):
        cursor.execute(
            """
            SELECT body_exobio_scans.*
            FROM body_exobio_scans
            JOIN bodies 
                ON body_exobio_scans.database_body_id = bodies.database_body_id
            WHERE bodies.database_system_id = ?
            """,
            (database_system_id,)
        )
        return cursor.fetchall()


if __name__ == '__main__':
    adapter = ArchivedSystemQueries()
    query = SqliteQuery()
    conn = adapter.establish_db_connection()
    adapter.initialize_schema(conn)
    original_payload = load_current_system_record()
    reconstructed_payload = adapter.get_archived_system_info(conn, 38562352187)

    if original_payload is None:
        raise ValueError(
            "Original system returned no payload."
        )

    if reconstructed_payload is None:
        raise ValueError("Archived system reconstruction returned no payload.")

    adapter._compare_fullstarsystem_payloads(original_payload, reconstructed_payload)

    print("FullStarSystemPayload round-trip validation passed.")
    adapter.close_db_connection(conn)