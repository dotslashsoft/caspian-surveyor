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
    body_ascending_node: float
    body_mean_anomaly: float


@dataclass
class ReboundBarycentre:
    system_address: int
    body_id: int
    scan_timestamp: int
    periapsis: float | None
    semi_major_axis: float | None
    eccentricity: float | None
    orbital_inclination: float | None
    orbital_period: float | None
    ascending_node: float | None
    mean_anomaly: float | None



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


    def _return_barycentres_dict(self, payload: FullStarSystemPayload) -> dict[str, BarycentreInfo]:
        if payload is not None:
            return payload.barycentres


    def construct_rebound_physorb_dict(
            self,
            bodies: dict[str, CelestialBody],
            barycentres: dict[str, BarycentreInfo]
    ) -> dict[str, Rebound | ReboundBarycentre]:
        
        rebound_bodies = {}
        for body_obj in bodies.values():

            if body_obj.body_mass is None:
                continue

            if body_obj.body_star_type is not None:
                rebound_mass = body_obj.body_mass
            else:
                rebound_mass = body_obj.body_mass / SOLAR_MASS_CONVERSION

            celestial_physorb_dict = {
                "body_id": body_obj.body_id,
                "body_scan_timestamp": body_obj.body_scan_timestamp,
                "body_name": body_obj.body_name,
                "body_parents": body_obj.body_parents,
                "body_mass": rebound_mass,
                "body_periapsis": body_obj.body_periapsis,
                "body_semi_major_axis": body_obj.body_semi_major_axis,
                "body_eccentricity": body_obj.body_eccentricity,
                "body_orbital_inclination": body_obj.body_orbital_inclination,
                "body_ascending_node": body_obj.body_ascending_node,
                "body_mean_anomaly": body_obj.body_mean_anomaly,
            }


            rebound_data = Rebound(
                **celestial_physorb_dict
            )

            rebound_body_id = body_obj.body_id
            rebound_bodies[rebound_body_id] = rebound_data

        for barycentre_obj in barycentres.values():
            barycentre_body_id = barycentre_obj.body_id
            rebound_bodies[barycentre_body_id] = barycentre_obj

        print(barycentres.values())

        
        return rebound_bodies
    

    def build_rebound_bodies_dict(self) -> dict[str, Rebound | ReboundBarycentre]:
        payload = self.get_fullstarsystempayload(38562352187)
        if payload is not None:
            bodies = self._return_bodies_dict(payload)
            barycentres = self._return_barycentres_dict(payload)

        rebound_bodies_dict = self.construct_rebound_physorb_dict(bodies, barycentres)

        return rebound_bodies_dict
        


if __name__ == '__main__':
    mapping = CaspianReboundMappings()
    pprint(mapping.build_rebound_bodies_dict())
