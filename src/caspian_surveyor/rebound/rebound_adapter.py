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

        self.temp_sim = rebound.Simulation()
        self.temp_sim.units = ("AU", "yr", "Msun")

    def get_system_data(
            self,
            system_address: int
    ) -> dict[int, dict[str, Any]]:
        return self.handler.prepare_system_data(system_address)

    # leaf barycentres: a barycentre whose immediate children contain no further barycentres.
    def _walk_system_hierarchy(
            self,
            system_data: dict[int, dict[str, Any]],
            object_id: int = 0,
            depth: int = 0,
    ):
        object_data = system_data[object_id]

        print(
            "...." * depth,
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

    def _get_leaf_barycentres(
            self,
            system_data: dict[int, dict[str, Any]],
            object_id: int = 0,
    ) -> list[int]:

        object_data = system_data[object_id]
        leaf_barycentres = []

        for child_id in object_data["immediate_children"]:
            leaf_barycentres.extend(
                self._get_leaf_barycentres(
                    system_data,
                    child_id,
                )
            )

        if object_data["type"] != "barycentre":
            return leaf_barycentres

        if object_id == 0:
            return leaf_barycentres

        children = object_data["immediate_children"]

        if all(system_data[child_id]["type"] == "body" for child_id in children):
            leaf_barycentres.append(object_id)

        return leaf_barycentres

    def _calculate_relative_semi_major_axis(
            self,
            primary_semi_major_axis: float,
            orbiting_semi_major_axis: float,
    ) -> float:
        return primary_semi_major_axis + orbiting_semi_major_axis

    def _construct_leaf_barycentre_subsystems(
            self,
            system_data: dict[int, dict[str, Any]],
            leaf_barycentres: list[int]
    ):
        for barycentre_id in leaf_barycentres:
            child_ids = system_data[barycentre_id]["immediate_children"]

            temp_sim = self._construct_two_body_subsystem(
                system_data,
                child_ids,
            )

    def _construct_two_body_subsystem(
            self,
            system_data,
            child_ids: list[int]
    ):
        temp_sim = rebound.Simulation()
        temp_sim.units = ("AU", "yr", "Msun")

        primary_child = system_data[child_ids[0]]
        orbiting_child = system_data[child_ids[1]]

        relative_semi_major_axis = self._calculate_relative_semi_major_axis(
            primary_child["semi_major_axis"],
            orbiting_child["semi_major_axis"]
        )

        temp_sim.add(
            m=primary_child["mass"],
            name=primary_child["name"],
        )
        primary = temp_sim.particles[0]

        temp_sim.add(
            m=orbiting_child["mass"],
            a=relative_semi_major_axis,
            e=orbiting_child["eccentricity"],
            inc=orbiting_child["orbital_inclination"],
            Omega=orbiting_child["ascending_node"],
            omega=orbiting_child["periapsis"],
            M=orbiting_child["mean_anomaly"],
            name=orbiting_child["name"],
            primary=primary,
        )

        temp_sim.move_to_com()

        return temp_sim


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

    def _proof_of_concept(self, system_data):
        self.temp_sim = rebound.Simulation()
        self.temp_sim.units = ("AU", "yr", "Msun")

        body_nine = system_data[9]
        body_ten = system_data[10]

        relative_semi_major_axis = (
            body_nine["semi_major_axis"]
            + body_ten["semi_major_axis"]
        )

        self.temp_sim.add(
            m=body_nine["mass"],
            name=body_nine["name"],
        )

        primary = self.temp_sim.particles[0]

        self.temp_sim.add(
            m=body_ten["mass"],
            a=relative_semi_major_axis,
            e=body_ten["eccentricity"],
            inc=body_ten["orbital_inclination"],
            Omega=body_ten["ascending_node"],
            omega=body_ten["periapsis"],
            M=body_ten["mean_anomaly"],
            primary=primary,
        )

        self.temp_sim.move_to_com()

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
        self.temp_sim.start_server(port=1234)
        self.temp_sim.usleep = 100000

        print("Simulation running indefinitely.")
        print("Open http://localhost:1234")
        print("CTRL+C to stop.")

        try:
            self.temp_sim.integrate(float("inf"))

        except KeyboardInterrupt:
            print("\nSimulation stopped.")

        finally:
            self.temp_sim.stop_server()


if __name__ == '__main__':
    adapter = ReboundAdapter()

    system_data = adapter.get_system_data(527609567169)

    leaf_barycentres = adapter._get_leaf_barycentres(system_data)

    adapter._construct_leaf_barycentre_subsystems(system_data, leaf_barycentres)


    # if system_data is not None:
    #     body_data = adapter._get_non_stellar_bodies(system_data)