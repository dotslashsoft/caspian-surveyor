from pprint import pprint
from dataclasses import dataclass
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.cs_data_structures import CelestialBody, FullStarSystemPayload, BodyParentInfo, BarycentreInfo

SOLAR_MASS_CONVERSION=333029.70449


@dataclass
class Rebound:
    body_id: int
    body_scan_timestamp: int
    body_name: str
    body_parents: list[BodyParentInfo]
    body_mass: float
    body_periapsis: float
    body_semi_major_axis: float
    body_eccentricity: float
    body_orbital_inclination: float
    body_orbital_period: float
    body_ascending_node: float
    body_mean_anomaly: float


@dataclass
class ReboundBarycentre:
    system_address: int
    body_id: int
    scan_timestamp: int
    periapsis: float | None = None
    semi_major_axis: float | None = None
    eccentricity: float | None = None
    orbital_inclination: float | None = None
    orbital_period: float | None = None
    ascending_node: float | None = None
    mean_anomaly: float | None = None



class CaspianReboundMappings:

    def get_fullstarsystempayload(self, system_address) -> FullStarSystemPayload | None:
        system_query = ArchivedSystemQueries()
        connection = ConnectionManager()
        conn = connection.establish_db_connection()

        try:
            connection.initialize_schema(conn)
            payload = system_query.get_archived_system_info(conn, system_address)
            return payload

        finally:
            connection.close_db_connection(conn)


    def _return_bodies_dict(self, payload: FullStarSystemPayload) -> dict[str, CelestialBody]:
        if payload is not None:
            return payload.bodies


    def construct_rebound_bodies_dict(
            self,
            bodies: dict[str, CelestialBody],
    ) -> dict[int, Rebound]:
        
        rebound_bodies = {}
        for body_obj in bodies.values():

            if body_obj.body_mass is None:
                continue

            if body_obj.body_star_type is not None:
                rebound_mass = body_obj.body_mass
            else:
                rebound_mass = body_obj.body_mass / SOLAR_MASS_CONVERSION

            rebound_bodies_dict = {
                "body_id": body_obj.body_id,
                "body_scan_timestamp": body_obj.body_scan_timestamp,
                "body_name": body_obj.body_name,
                "body_parents": body_obj.body_parents,
                "body_mass": rebound_mass,
                "body_periapsis": body_obj.body_periapsis,
                "body_semi_major_axis": body_obj.body_semi_major_axis,
                "body_eccentricity": body_obj.body_eccentricity,
                "body_orbital_inclination": body_obj.body_orbital_inclination,
                "body_orbital_period": body_obj.body_orbital_period,
                "body_ascending_node": body_obj.body_ascending_node,
                "body_mean_anomaly": body_obj.body_mean_anomaly,
            }


            rebound_data = Rebound(
                **rebound_bodies_dict
            )

            rebound_body_id = body_obj.body_id
            rebound_bodies[rebound_body_id] = rebound_data
        
        return rebound_bodies


    def _return_barycentres_dict(self, payload: FullStarSystemPayload) -> dict[str, BarycentreInfo]:
        if payload is not None:
            return payload.barycentres
        

    def construct_rebound_barycentres_dict(self, barycentres: dict[str, BarycentreInfo]) -> dict[int, ReboundBarycentre]:
        rebound_barycentres = {}

        for barycentre_obj in barycentres.values():
            rebound_barycentres_dict = {
                "system_address": barycentre_obj.system_address,
                "body_id": barycentre_obj.body_id,
                "scan_timestamp": barycentre_obj.scan_timestamp,
                "semi_major_axis": barycentre_obj.semi_major_axis,
                "eccentricity": barycentre_obj.eccentricity,
                "orbital_inclination": barycentre_obj.orbital_inclination,
                "periapsis": barycentre_obj.periapsis,
                "orbital_period": barycentre_obj.orbital_period,
                "ascending_node": barycentre_obj.ascending_node,
                "mean_anomaly": barycentre_obj.mean_anomaly,
            }

            rebound_barycentre_data = ReboundBarycentre(
                **rebound_barycentres_dict
            )

            rebound_body_id = barycentre_obj.body_id
            rebound_barycentres[rebound_body_id] = rebound_barycentre_data

        return rebound_barycentres

    def build_rebound_bodies_dict(self) -> dict[int, Rebound]:
        payload = self.get_fullstarsystempayload(38562352187)
        if payload is not None:
            bodies = self._return_bodies_dict(payload)

        self.rebound_bodies_dict = self.construct_rebound_bodies_dict(bodies)

        return self.rebound_bodies_dict


    def build_rebound_barycentres_dict(self) -> dict[int, ReboundBarycentre]:
        payload = self.get_fullstarsystempayload(38562352187)
        if payload is not None:
            barycentres = self._return_barycentres_dict(payload)

        self.rebound_barycentres_dict = self.construct_rebound_barycentres_dict(barycentres)

        return self.rebound_barycentres_dict


    def resolve_immediate_parent(self, 
            body_parents: list[BodyParentInfo],
            rebound_bodies: dict[int, Rebound], 
            rebound_barycentres: dict[int, ReboundBarycentre]
        ):
        
        if not body_parents:
            return None

        parent_info = body_parents[0]

        if parent_info.parent_type == "Null":
            return rebound_barycentres[parent_info.parent_body_id]

        if parent_info.parent_type in ("Star", "Planet"):
            return rebound_bodies[parent_info.parent_body_id]

        raise ValueError(f"Unknown parent type: {parent_info.parent_type}")


    def resolve_rebound_parents(self, rebound_bodies, rebound_barycentres):
        for rebound_body in rebound_bodies.values():

            parent = self.resolve_immediate_parent(
                rebound_body.body_parents,
                rebound_bodies,
                rebound_barycentres
            )

            if parent is None:
                print(f"{rebound_body.body_id} -> None")
            else:
                print(
                    f"{rebound_body.body_id} -> "
                    f"{type(parent).__name__} {parent.body_id}"
                )

    def infer_barycentre_immediate_parents(
            self,
            rebound_bodies: dict[int, Rebound],
        ) -> dict[int, BodyParentInfo]:

        resolved_barycentre_parents = {}
        for rebound_body in rebound_bodies.values():

            body_parents = rebound_body.body_parents
            if not body_parents:
                continue

            immediate_parent = body_parents[0]
            if immediate_parent.parent_type != "Null":
                continue

            barycentre_id = immediate_parent.parent_body_id
            if len(body_parents) > 1:
                barycentre_parent = body_parents[1]
                resolved_barycentre_parents[barycentre_id] = barycentre_parent

        return resolved_barycentre_parents
        
    def resolve_rebound_barycentre_parents(
            self,
            rebound_bodies: dict[int, Rebound],
            rebound_barycentres: dict[int, ReboundBarycentre]
        ):

        barycentre_parents = self.infer_barycentre_immediate_parents(rebound_bodies)

        for barycentre_id, parent_info in barycentre_parents.items():

            if parent_info.parent_type == "Null":
                parent = rebound_barycentres[parent_info.parent_body_id]

            elif parent_info.parent_type in ("Star", "Planet"):
                parent = rebound_bodies[parent_info.parent_body_id]

            else:
                raise ValueError(
                    f"Unknown barycentre parent type: "
                    f"{parent_info.parent_type}"
                )

            print(
                f"{barycentre_id} -> "
                f"{type(parent).__name__} {parent.body_id}"
            )


if __name__ == '__main__':
    mapping = CaspianReboundMappings()
    rebound_bodies = mapping.build_rebound_bodies_dict()
    pprint(rebound_bodies, sort_dicts=False)
    rebound_barycentres = mapping.build_rebound_barycentres_dict()
    pprint(rebound_barycentres, sort_dicts=False)

    # mapping.resolve_rebound_parents(rebound_bodies, rebound_barycentres)
    # resolved_barycentre_parents = mapping.infer_barycentre_immediate_parents(rebound_bodies)

    # mapping.resolve_rebound_barycentre_parents(rebound_bodies, rebound_barycentres)