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
        """Query SQLite for a system and reconstruct its FullStarSystemPayload.

        Args:
            system_address (int): Address of the system to reconstruct.

        Returns:
            FullStarSystemPayload | None: Reconstructed system data if successful,
            otherwise None.
        """
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
        """Return dictionary containing CelestialBody data for a system.

        Args:
            system_record (FullStarSystemPayload): All data that Caspian Surveyor
                has on record. Arg is returned from `_get_fullstarsystempayload`.

        Returns:
            dict[str, CelestialBody]: Celestial body data for the system.
        """
        if system_record is not None:
            return system_record.bodies

    def _return_barycentre_dict(self, system_record: FullStarSystemPayload) -> dict[str, BarycentreInfo]:
        """Return dictionary containing BarycentreInfo data for a system.

        Args:
            system_record (FullStarSystemPayload): All data that Caspian Surveyor
                has on record. Arg is returned from `_get_fullstarsystempayload`.

        Returns:
            dict[str, BarycentreInfo]: BarycentreInfo body data for the system.
        """
        if system_record is not None:
            return system_record.barycentres

    def _merge_dicts(
            self,
            sorted_bodies: dict[int, dict[str, Any]],
            sorted_barycentres: dict[int, dict[str, Any]]
    ) -> dict[int, dict[str, Any]]:
        """Merge body and barycentre dictionaries and sort by record ID."""
        merged_dicts = sorted_bodies | sorted_barycentres

        return dict(
            sorted(merged_dicts.items(), key=lambda item: item[0])
        )

    def _calculate_rebound_mass(self, body_obj: CelestialBody) -> float | None:
        """Calculate non-stellar body mass for REBOUND."""
        if body_obj.body_star_type is not None:
            return body_obj.body_mass

        if body_obj.body_mass is not None:
            return body_obj.body_mass / SOLAR_MASS_CONVERSION

        return

    def _convert_to_radians(self, value) -> float | None:
        """Convert value to radians for REBOUND."""
        if value is not None:
            return math.radians(value)

    def _parent_info_to_list(self, parents: list[BodyParentInfo]):
        """Create a list of parent body ID's."""
        parent_list = []
        if parents is not None:
            for parent in parents:
                parent_list.append(parent.parent_body_id)

        return parent_list

    def _return_filtered_celestial_bodies(self, bodies: dict[str, CelestialBody]) -> dict[int, Any]:
        """Filter out non-celestial body objects from CelestialBody data."""
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

    def _create_barycentre_dict(
            self,
            barycentres: dict[str, BarycentreInfo]
    ) -> dict[int, dict[str, Any]]:
        """Create dictionary containing system barycentre information."""
        barycentre_dict = {}

        for barycentre_obj in barycentres.values():

            barycentre_record = {
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

            barycentre_id = barycentre_obj.body_id
            barycentre_dict[barycentre_id] = barycentre_record

        return barycentre_dict

    def _append_body_descendant(self,
            merged_dict: dict[int, dict],
            body: tuple[int, str],
            parent: int
    ) -> None:
        merged_dict[parent]["descendants"].append(body)

    def _get_body_descendants(self, merged_dicts: dict[int, dict]):
        for each_entry in merged_dicts.values():
            if each_entry["ancestors"] is not None:
                for each_parent in each_entry["ancestors"]:
                    self._append_body_descendant(
                        merged_dicts,
                        (each_entry["id"], each_entry["name"]),
                        each_parent
                    )

    def _append_immediate_children(
            self,
            merged_dicts: dict[int, dict]
    ) -> None:
        for each_body in merged_dicts.values():
            immediate_parent = each_body["immediate_parent"]

            if immediate_parent is not None:
                body_record_id = each_body["id"]
                merged_dicts[immediate_parent]["immediate_children"].append(body_record_id)

    def _set_barycentre_immediate_parents(
            self,
            merged_dicts: dict[int, dict[str, Any]]
    ) -> None:
        """Set the immediate parent for each barycentre."""

        for body in merged_dicts.values():
            ancestors = body["ancestors"]

            if ancestors is None:
                continue

            for child_id, parent_id in zip(ancestors, ancestors[1:]):
                if merged_dicts[child_id]["type"] == "barycentre":
                    merged_dicts[child_id]["immediate_parent"] = parent_id

    def _rebuild_immediate_children(self, merged_dicts: dict[int, dict]):
        for each_body in merged_dicts.values():
            each_body["immediate_children"] = []

        for each_body in merged_dicts.values():

            immediate_parent = each_body["immediate_parent"]

            if immediate_parent is not None:
                merged_dicts[immediate_parent]["immediate_children"].append(
                    each_body["id"]
                )

    def _prepare_system_hierarchy(self, merged_dict: dict[int, dict]):

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
        self._set_barycentre_immediate_parents(sorted_rebound)
        self._rebuild_immediate_children(sorted_rebound)

        return sorted_rebound

if __name__ == '__main__':
    handler = CaspianDataHandler()
    archive = ArchivedSystemQueries()

    system_archive = handler._get_fullstarsystempayload(527609567169)

    if system_archive is not None:
        bodies = handler._return_celestial_body_dict(system_archive)
        barycentres = handler._return_barycentre_dict(system_archive)

    rebound_bodies_dict = handler._return_filtered_celestial_bodies(bodies)
    rebound_barycentres_dict = handler._create_barycentre_dict(barycentres)

    merged_dict = handler._merge_dicts(rebound_bodies_dict, rebound_barycentres_dict)

    sorted_rebound = handler._prepare_system_hierarchy(merged_dict)
    pprint(sorted_rebound, sort_dicts=False)