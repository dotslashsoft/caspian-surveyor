import sqlite3
import logging
from dataclasses import asdict
import json
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.cs_data_structures import (
    FullStarSystemPayload, CelestialBody, SystemInfo, BodyParentInfo, BodyMaterialInfo,
    BodySignalInfo, BodyGenusInfo, ExoBioScanInfo, SystemSummaryInfo
)
from caspian_surveyor.runtime.cs_runtime import load_current_system_record, write_current_system_record
from caspian_surveyor.db.sql_statements import (
    GET_SYSTEM_INFO, GET_SYSTEM_BODIES, GET_SYSTEM_PARENTS,
    GET_SYSTEM_MATERIALS, GET_SYSTEM_PHYSORB, GET_SYSTEM_SIGNALS,
    GET_SYSTEM_GENUSES, GET_SYSTEM_EXOBIO
)

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self) -> None:
        self.manager = ConnectionManager()
        self.database_schema = self.manager.database_schema
        self.database_file = self.manager.database_file


class ArchivedSystemQueries:
    """
    Class containing methods to retrieve previously archived Caspian system state.
    """

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
                "body_scan_timestamp": body_obj[3],
                "body_name": body_obj[4],
                "body_planet_class": body_obj[5],
                "body_star_type": body_obj[6],
                "body_terraform_state": body_obj[7],
                "body_was_discovered": bool(body_obj[8]),
                "body_was_mapped": bool(body_obj[9]),
                "body_was_footfalled": bool(body_obj[10]),
                "body_landable": bool(body_obj[11]),
                "body_dss_scan_complete": bool(body_obj[12]),
                "body_tidal_lock": bool(body_obj[13]),
                "body_atmosphere": body_obj[14],
                "body_atmosphere_type": body_obj[15],
                "body_distance_from_arrival": body_obj[16],
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
                "body_mass": physorb[2],
                "body_surface_gravity": physorb[3],
                "body_surface_pressure": physorb[4],
                "body_surface_temperature": physorb[5],
                "body_semi_major_axis": physorb[6],
                "body_eccentricity": physorb[7],
                "body_orbital_inclination": physorb[8],
                "body_orbital_period": physorb[9],
                "body_ascending_node": physorb[10],
                "body_mean_anomaly": physorb[11],
                "body_rotational_period": physorb[12],
                "body_axial_tilt": physorb[13],
                "body_periapsis": physorb[14],
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


    def get_archived_system_info(self, connection: sqlite3.Connection, system_address: int):
        cursor = connection.cursor()

        database_system_id = self.get_system_id(
            cursor,
            system_address
        )
        if database_system_id is None:
            return None

        system = self._query_archive_fetchone(cursor, GET_SYSTEM_INFO, (database_system_id,))
        bodies = self._query_archive_fetchall(cursor, GET_SYSTEM_BODIES, (database_system_id,))
        parents = self._query_archive_fetchall(cursor, GET_SYSTEM_PARENTS, (database_system_id,))
        materials = self._query_archive_fetchall(cursor, GET_SYSTEM_MATERIALS, (database_system_id,))
        physorb = self._query_archive_fetchall(cursor, GET_SYSTEM_PHYSORB, (database_system_id,))
        signals = self._query_archive_fetchall(cursor, GET_SYSTEM_SIGNALS, (database_system_id,))
        genuses = self._query_archive_fetchall(cursor, GET_SYSTEM_GENUSES, (database_system_id,))
        exobio = self._query_archive_fetchall(cursor, GET_SYSTEM_EXOBIO, (database_system_id,))


        system_info = self._construct_archived_system(system)
        
        bodies_by_database_id, bodies_by_elite_id = (
            self._construct_archived_bodies(bodies)
        )
        self._construct_archived_body_parents(parents, bodies_by_database_id)
        self._construct_archived_body_materials(materials, bodies_by_database_id)
        self._construct_archived_body_physorb(physorb, bodies_by_database_id)
        self._construct_archived_body_signals(signals, bodies_by_database_id)
        self._construct_archived_body_genuses(genuses, bodies_by_database_id)
        self._construct_archived_body_exobio(exobio, bodies_by_database_id)

        system_summary_info = self._construct_system_summary_info(bodies_by_elite_id)
        system_summary_info.system_fss_complete = bool(system["system_fss_complete"])

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


    def _query_archive_fetchone(self, cursor: sqlite3.Cursor, sql_statement: str, parameters: tuple = ()) -> sqlite3.Row:
        cursor.execute(sql_statement, parameters)
        return cursor.fetchone()


    def _query_archive_fetchall(self, cursor: sqlite3.Cursor, sql_statement: str, parameters: tuple = ()) -> list[sqlite3.Row]:
        cursor.execute(sql_statement, parameters)
        return cursor.fetchall()



def execute_query_statement(connection: sqlite3.Connection, query_statement: str) -> list[sqlite3.Row]:
    cursor = connection.cursor()
    try:
        cursor.execute(query_statement)
        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Database query failed: {e}")
        raise



if __name__ == '__main__':
    connection = Connection()
    adapter = ArchivedSystemQueries()
    conn = connection.manager.establish_db_connection()
    connection.manager.initialize_schema(conn)

    original_payload = load_current_system_record()
    

    if original_payload is None:
        raise ValueError(
            "Original system returned no payload."
        )
    system_address = original_payload.system.system_address
    reconstructed_payload = adapter.get_archived_system_info(conn, system_address=38562352187)
    if reconstructed_payload is None:
        raise ValueError("Archived system reconstruction returned no payload.")

    adapter._compare_fullstarsystem_payloads(original_payload, reconstructed_payload)
    print("FullStarSystemPayload round-trip validation passed.")
    write_current_system_record(reconstructed_payload)

    connection.manager.close_db_connection(conn)