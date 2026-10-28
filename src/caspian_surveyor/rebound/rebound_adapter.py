import rebound
import logging
from pprint import pprint
from caspian_surveyor.rebound.caspian_to_rebound_data_prep import CaspianDataHandler
from typing import Any

logger = logging.getLogger(__name__)


class ReboundAdapter:
    def __init__(self) -> None:
        self.handler = CaspianDataHandler()
        self.sim = rebound.Simulation()
        self.sim.units = ("AU", "yr", "Msun")

    def get_system_data(
            self,
            system_address: int
    ) -> dict[int, dict[str, Any]]:
        return self.handler.prepare_system_data(system_address)

    def _walk_system_hierarchy(
            self,
            system_data: dict[int, dict[str, Any]],
            object_id: int = 0,
            depth: int = 0,
    ) -> None:
        object_data = system_data[object_id]

        print(
            "    " * depth,
            object_data["id"],
            object_data["type"],
            object_data["name"],
        )

        for child_id in object_data["immediate_children"]:
            self._walk_system_hierarchy(
                system_data,
                child_id,
                depth + 1,
            )

    def _return_root_stellar_body(
            self,
            system_data: dict[int, dict[str, Any]]
    ) -> dict[str, Any]:
        return system_data[0]

    def _add_system_root(self, root_object: dict[str, Any]) -> None:
        if root_object["type"] == "barycentre":
            return

        self.sim.add(
            m=root_object["mass"],
            name=root_object["name"],
        )

    def _get_non_stellar_bodies(
            self,
            system_data: dict[int, dict[str, Any]]
    ) -> dict[int, dict[str, Any]]:
        non_stellar_bodies: dict[int, dict[str, Any]] = {}

        for object_data in system_data.values():
            if object_data["type"] != "body":
                continue

            if object_data["star_type"] is not None:
                continue

            body = object_data

            non_stellar_body_id = body["id"]
            non_stellar_bodies[non_stellar_body_id] = body

        return non_stellar_bodies


    def _add_non_stellar_bodies(self, non_stellar_bodies: dict[int, dict[str, Any]]):
        for body_record in non_stellar_bodies.values():
            immediate_parent = body_record["immediate_parent"]
            self._add_non_stellar_body(
                body_record,
                body_record["immediate_parent"]
            )

    def _add_non_stellar_body(self, body_record: dict[str, Any], primary):
        self.sim.add(
            m=body_record["mass"],
            a=body_record["semi_major_axis"],
            e=body_record["eccentricity"],
            inc=body_record["orbital_inclination"],
            Omega=body_record["ascending_node"],
            omega=body_record["periapsis"],
            M=body_record["mean_anomaly"],
            name=body_record["name"],
            primary=primary,
        )


    def start_rebound_visualization(self):
        self.sim.start_server(port=1234)
        self.sim.usleep = 2500

        print("Simulation running indefinitely.")
        print("Open http://localhost:1234")
        print("CTRL+C to stop.")

        try:
            self.sim.integrate(float("inf"))

        except KeyboardInterrupt:
            print("\nSimulation stopped.")

        finally:
            self.sim.stop_server()


if __name__ == '__main__':
    adapter = ReboundAdapter()

    system_data = adapter.get_system_data(527609567169)

    adapter._walk_system_hierarchy(system_data)

    if system_data is not None:
        body_data = adapter._get_non_stellar_bodies(system_data)