from pprint import pprint
import logging
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.cs_data_structures import FullStarSystemPayload, CelestialBody, BodyParentInfo, BarycentreInfo
import math
from typing import Any

logger = logging.getLogger(__name__)

SOLAR_MASS_CONVERSION=333029.70449
AU_IN_METERS = 149_597_870_700


class CaspianDataHandler:
    def _get_fullstarsystempayload(self, system_address) -> FullStarSystemPayload | None:
        system_query = ArchivedSystemQueries()
        connection = ConnectionManager()
        conn = connection.establish_db_connection()

        try:
            connection.initialize_schema(conn)
            payload = system_query.get_archived_system_info(conn, system_address)

            return payload
        finally:
            connection.close_db_connection(conn)

    def _return_celestial_body_dict(self, system_record: FullStarSystemPayload) -> dict[str, CelestialBody]:
        if system_record is not None:
            return system_record.bodies

    def _return_barycentre_dict(self, system_record: FullStarSystemPayload) -> dict[str, BarycentreInfo]:
        if system_record is not None:
            return system_record.barycentres

    def _merge_dicts(self, sorted_bodies: dict[int, dict], sorted_barycentres: dict[int, dict]):
        merged_dicts = sorted_bodies | sorted_barycentres
        return dict(
            sorted(merged_dicts.items(), key=lambda item: item[0])
        )

    def _calculate_rebound_mass(self, body_obj: CelestialBody) -> float | None:
            if body_obj.body_star_type is not None:
                return body_obj.body_mass

            if body_obj.body_mass is not None:
                return body_obj.body_mass / SOLAR_MASS_CONVERSION

            return

    def _convert_to_radians(self, value) -> float | None:
        if value is not None:
            return math.radians(value)

    def _parent_info_to_list(self, parents: list[BodyParentInfo]):
        parent_list = []
        if parents is not None:
            for parent in parents:
                parent_list.append(parent.parent_body_id)

        return parent_list

    def _return_filtered_celestial_bodies(self, bodies: dict[str, CelestialBody]) -> dict[int, Any]:
        rebound_dict = {}

        for body_obj in bodies.values():
            if body_obj.body_mass is None:
                continue

            if body_obj.body_star_type is not None:
                rebound_mass = body_obj.body_mass

            else:
                rebound_mass = self._calculate_rebound_mass(body_obj)

            semi_major_axis = None
            if body_obj.body_semi_major_axis is not None:
                semi_major_axis = body_obj.body_semi_major_axis / AU_IN_METERS


            periapsis = self._convert_to_radians(body_obj.body_periapsis)
            orbital_inclination = self._convert_to_radians(body_obj.body_orbital_inclination)
            ascending_node = self._convert_to_radians(body_obj.body_ascending_node)
            mean_anomaly = self._convert_to_radians(body_obj.body_mean_anomaly)

            parents_list = self._parent_info_to_list(body_obj.body_parents)

            rebound_bodies_dict = {
                "id": body_obj.body_id,
                "type": "body",
                "scan_timestamp": body_obj.body_scan_timestamp,
                "name": body_obj.body_name,
                "ancestors": parents_list,
                "descendants": [],
                "immediate_parent": parents_list[0],
                "immediate_children": [],
                "mass": rebound_mass,
                "periapsis": periapsis,
                "semi_major_axis": semi_major_axis,
                "eccentricity": body_obj.body_eccentricity,
                "orbital_inclination": orbital_inclination,
                "orbital_period": body_obj.body_orbital_period,
                "ascending_node": ascending_node,
                "mean_anomaly": mean_anomaly,
            }

            rebound_body_id = body_obj.body_id
            rebound_dict[rebound_body_id] = rebound_bodies_dict

        return rebound_dict

    def _return_barycentres(self, barycentres: dict[str, BarycentreInfo]) -> dict[int, Any]:
        rebound_dict = {}

        for barycentre_obj in barycentres.values():

            rebound_barycentres_dict = {
                "id": barycentre_obj.body_id,
                "type": "barycentre",
                "scan_timestamp": barycentre_obj.scan_timestamp,
                "name": barycentre_obj.body_id,
                "ancestors": None,
                "descendants": [],
                "immediate_parent": None,
                "immediate_children": [],
                "mass": 0,
                "periapsis": math.radians(barycentre_obj.periapsis),
                "semi_major_axis": barycentre_obj.semi_major_axis / AU_IN_METERS,
                "eccentricity": barycentre_obj.eccentricity,
                "orbital_inclination": math.radians(barycentre_obj.orbital_inclination),
                "orbital_period": barycentre_obj.orbital_period,
                "ascending_node": math.radians(barycentre_obj.ascending_node),
                "mean_anomaly": math.radians(barycentre_obj.mean_anomaly),
            }

            rebound_id = barycentre_obj.body_id
            rebound_dict[rebound_id] = rebound_barycentres_dict

        return rebound_dict

    def _map_body_descendants(self,
            merged_dict: dict[int, dict],
            body: tuple[int, str],
            parent: int
        ) -> None:
        merged_dict[parent]["descendants"].append(body)

    def _get_body_descendants(self, merged_dicts: dict[int, dict]):
        for each_entry in merged_dicts.values():
            if each_entry["ancestors"] is not None:
                for each_parent in each_entry["ancestors"]:
                    self._map_body_descendants(
                        merged_dicts,
                        (each_entry["id"], each_entry["name"]),
                        each_parent
                    )

    def _get_immediate_children(self, merged_dicts: dict[int, dict]) -> None:
        for each_body in merged_dicts.values():
            if each_body["immediate_parent"] != []:
                immediate_parent = each_body["immediate_parent"]
                if immediate_parent is not None:
                    body_record_id = each_body["id"]
                    # print(f"Body {body_record_id}'s immediate parent is {immediate_parent}")
                    merged_dicts[immediate_parent]["immediate_children"].append(body_record_id)

    def _get_barycentres_list(self, merged_dicts: dict[int, dict]) -> list[int]:
        barycentres_list = []

        for each_body in merged_dicts.values():
            if each_body["type"] == "barycentre":
                barycentres_list.append(each_body["id"])

        return barycentres_list

    def _get_barycentre_immediate_children(
            self,
            merged_dicts: dict[int, dict],
            barycentre_list: list[int]
    ) -> None:
        seen_relationships = set()
        for barycentre in barycentre_list:
            for each_body in merged_dicts.values():

                ancestors = each_body["ancestors"]

                if ancestors is not None:
                    if barycentre in ancestors:

                        barycentre_index = ancestors.index(barycentre)
                        immediate_parent_index = barycentre_index + 1

                        if immediate_parent_index < len(ancestors):
                            immediate_parent = ancestors[immediate_parent_index]
                            relationship = (barycentre, immediate_parent)

                            if relationship not in seen_relationships:
                                seen_relationships.add(relationship)
                                merged_dicts[barycentre]["immediate_parent"] = immediate_parent

    def _get_barycentre_parents(self, merged_dicts: dict[int, dict]):
        for each_body in merged_dicts.values():
            each_body["immediate_children"] = []

        for each_body in merged_dicts.values():

            immediate_parent = each_body["immediate_parent"]

            if immediate_parent is not None:
                merged_dicts[immediate_parent]["immediate_children"].append(
                    each_body["id"]
                )

    def _calculate_com(self, merged_dict, merged_dict_ids=None):
        if merged_dict_ids is None:
            merged_dict_ids = merged_dict.keys()

        total_mass = 0.0
        com_x, com_y, com_z = 0.0, 0.0, 0.0

        for id in merged_dict_ids:
            object = merged_dict[id]

            if object['type'] == 'barycentre' or object['mass'] <= 0:
                continue

            x = object.get('x', 0.0)
            y = object.get('y', 0.0)
            z = object.get('z', 0.0)

            mass = object['mass']
            total_mass += mass
            com_x += x * mass
            com_y += y * mass
            com_z += z * mass

        if total_mass == 0:
            return (0.0, 0.0, 0.0)

        return (com_x / total_mass, com_y / total_mass, com_z / total_mass)

    def get_system_root(self, merged_dict: dict[int, dict]):

        if 0 in merged_dict:
            print("Found barycentre root.")

        else:
            print("need to calculate COM.")
            print("creating barycenter 0")

            merged_dict[0] = {
                "id": 0,
                "type": "barycentre",
                "scan_timestamp": 0,
                "name": "root",
                "ancestors": None,
                "descendants": [],
                "immediate_parent": None,
                "immediate_children": [],
                "mass": 0,
                "periapsis": 0,
                "semi_major_axis": 0,
                "eccentricity": 0,
                "orbital_inclination": 0,
                "orbital_period": 0,
                "ascending_node": 0,
                "mean_anomaly": 0,
            }

        sorted_rebound = dict(
            sorted(merged_dict.items(), key=lambda item: item[0])
        )

        self._get_body_descendants(sorted_rebound)
        self._get_immediate_children(sorted_rebound)

        barycentre_list = self._get_barycentres_list(sorted_rebound)

        self._get_barycentre_immediate_children(
            sorted_rebound,
            barycentre_list
        )
        self._get_barycentre_parents(sorted_rebound)

        return sorted_rebound

if __name__ == '__main__':
    handler = CaspianDataHandler()
    archive = ArchivedSystemQueries()

    system_archive = handler._get_fullstarsystempayload(527609567169)

    if system_archive is not None:
        bodies = handler._return_celestial_body_dict(system_archive)
        barycentres = handler._return_barycentre_dict(system_archive)

    rebound_bodies_dict = handler._return_filtered_celestial_bodies(bodies)
    rebound_barycentres_dict = handler._return_barycentres(barycentres)

    merged_dict = handler._merge_dicts(rebound_bodies_dict, rebound_barycentres_dict)

    sorted_rebound = handler.get_system_root(merged_dict)
    pprint(sorted_rebound, sort_dicts=False)

    # com = handler._calculate_com(sorted_rebound)
    # print(com)