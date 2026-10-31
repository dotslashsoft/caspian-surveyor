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

    def _group_system_subsystems(self, system_data):
        physical_body_subsystems = {}
        barycentre_subsystems = {}

        for parent_id, parent_record in system_data.items():
            child_ids = parent_record["immediate_children"]

            if not child_ids:
                continue

            if parent_record["type"] == "body":
                physical_body_subsystems[parent_id] = child_ids

            elif parent_record["type"] == "barycentre":
                barycentre_subsystems[parent_id] = child_ids

        return physical_body_subsystems, barycentre_subsystems


    def _get_subsystem_construction_order(
            self,
            physical_body_subsystems: dict[int, list[int]],
            barycentre_subsystems: dict[int, list[int]],
    ) -> list[list[int]]:
        subsystem_groups = physical_body_subsystems | barycentre_subsystems
        pending = set(subsystem_groups)

        construction_order = []
        while pending:
            ready = sorted(
                parent_id
                for parent_id in pending
                if not any(
                    child_id in pending
                    for child_id in subsystem_groups[parent_id]
                )
            )
            if not ready:
                raise ValueError("Unable to resolve subsystem dependencies.")

            construction_order.append(ready)
            pending.difference_update(ready)

        return construction_order

    def _process_construction_order(self, system_data: dict, construction_order: list):
        resolved_barycentre_subsystems = {}
        resolved_physical_subsystems = {}

        for stage in construction_order:
            for id in stage:
                if system_data[id]["type"] == "barycentre":
                    barycentre_id = id
                    barycentre_children = system_data[barycentre_id]["immediate_children"]

                    resolved_barycentre_subsystem = {
                        "barycentre_id": barycentre_id,
                        "particles": {},
                    }

                    temp_sim = self._construct_barycentre_subsystem(
                        system_data,
                        barycentre_id,
                        barycentre_children,
                        resolved_barycentre_subsystems
                    )

                    self._store_temp_sim_data(
                        system_data,
                        barycentre_children,
                        resolved_barycentre_subsystem,
                        temp_sim,
                    )

                    resolved_barycentre_subsystems[barycentre_id] = resolved_barycentre_subsystem

                else:
                    physical_body_id = id
                    physical_body_children = system_data[physical_body_id]["immediate_children"]

                    print(f"{physical_body_id} is a physical body")
                    print(f"{physical_body_id}'s immediate children are {physical_body_children}")

                    resolved_physical_subsystem = {
                        "parent_body_id": physical_body_id,
                        "particles": {},
                    }

                    temp_sim = self._construct_physical_body_subsystem(
                        system_data,
                        physical_body_id,
                        physical_body_children
                    )

                    self._store_temp_sim_data(
                        system_data,
                        [physical_body_id, *physical_body_children],
                        resolved_physical_subsystem,
                        temp_sim,
                    )

                    resolved_physical_subsystems[physical_body_id] = resolved_physical_subsystem

        return resolved_barycentre_subsystems, resolved_physical_subsystems

    def _construct_physical_body_subsystem(
            self,
            system_data: dict,
            parent_id,
            child_ids: list
    ):
        temp_sim = rebound.Simulation()
        temp_sim.units = ("AU", "yr", "Msun")
        primary_parent_id = parent_id
        primary_body = system_data[primary_parent_id]
        physical_child_list = []

        for child in child_ids:
            if system_data[child]["type"] == "body":
                physical_child_list.append(child)
            else:
                print(f"Skipping resolved barycentre {child} for now.")
                continue

        orbiting_child_bodies = physical_child_list
        self._add_primary_physical_body(primary_body, temp_sim)

        primary = temp_sim.particles[0]
        for each_child in orbiting_child_bodies:
            child_body = system_data[each_child]

            temp_sim.add(
                m=child_body["mass"],
                a=child_body["semi_major_axis"],
                e=child_body["eccentricity"],
                inc=child_body["orbital_inclination"],
                Omega=child_body["ascending_node"],
                omega=child_body["periapsis"],
                M=child_body["mean_anomaly"],
                name=child_body["name"],
                primary=primary,
            )

        return temp_sim

    def _construct_barycentre_subsystem(
            self,
            system_data: dict,
            parent_id,
            child_ids: list,
            resolved_barycentre_subsystems: dict
    ):
        temp_sim = rebound.Simulation()
        temp_sim.units = ("AU", "yr", "Msun")

        if len(child_ids) > 2:
            print(f"processing barycentre with {len(child_ids)} immediate children")
            physical_child_list = []

            for child in child_ids:
                if system_data[child]["type"] == "body":
                    physical_child_list.append(child)
                else:
                    existing_subsystem = resolved_barycentre_subsystems[child]
                    # logic to load subsystem to current subsystem

            print(f"List of physical child bodies for {parent_id}: {physical_child_list}")

            child_primary = physical_child_list[0]
            child_primary_body = system_data[child_primary]
            orbiting_child_bodies = physical_child_list[1:]

            self._add_primary_physical_body(child_primary_body, temp_sim)

            primary = temp_sim.particles[0]
            for each_child in orbiting_child_bodies:
                child_body = system_data[each_child]

                print(f"Adding {child_body["name"]}...")
                temp_sim.add(
                    m=child_body["mass"],
                    a=child_body["semi_major_axis"],
                    e=child_body["eccentricity"],
                    inc=child_body["orbital_inclination"],
                    Omega=child_body["ascending_node"],
                    omega=child_body["periapsis"],
                    M=child_body["mean_anomaly"],
                    name=child_body["name"],
                    primary=primary,
                )

        elif len(child_ids) == 2:
            print(f"{child_ids} is == 2")
            print(f"treating {child_ids} as binary subsystem")

            child_primary = child_ids[0]
            child_primary_body = system_data[child_primary]
            orbiting_child_bodies = child_ids[1:]

            orbiting_child_id = child_ids[1]
            orbiting_child_body = system_data[orbiting_child_id]

            relative_semi_major_axis = child_primary_body["semi_major_axis"] + orbiting_child_body["semi_major_axis"]

            self._add_primary_physical_body(child_primary_body, temp_sim)

            primary = temp_sim.particles[0]

            temp_sim.add(
                m=orbiting_child_body["mass"],
                a=relative_semi_major_axis,
                e=orbiting_child_body["eccentricity"],
                inc=orbiting_child_body["orbital_inclination"],
                Omega=orbiting_child_body["ascending_node"],
                omega=orbiting_child_body["periapsis"],
                M=orbiting_child_body["mean_anomaly"],
                name=str(orbiting_child_body["name"]),
                primary=primary,
            )
        else:
            print(f"{child_ids} is  < 2")
            print(f"{child_ids} is gonna be weird as fuck")

        temp_sim.move_to_com()

        return temp_sim

    def _add_primary_physical_body(self, primary_physical_body, temp_sim):
        temp_sim.add(
            m=primary_physical_body["mass"],
            name=str(primary_physical_body["name"])
        )

    def _store_temp_sim_data(
            self,
            system_data,
            child_ids,
            resolved_barycentre_subsystem: dict,
            temp_sim
    ):
        for child_id in child_ids:
            if system_data[child_id]["type"] == "barycentre":
                print(f"Skipping barycentre {child_id}")
                continue

            child_name = system_data[child_id]["name"]
            particle = temp_sim.particles[child_name]

            resolved_barycentre_subsystem["particles"][child_id] = {
                "id": child_id,
                "name": child_name,
                "mass": particle.m,
                "x": particle.x,
                "y": particle.y,
                "z": particle.z,
                "vx": particle.vx,
                "vy": particle.vy,
                "vz": particle.vz,
            }

if __name__ == '__main__':
    adapter = ReboundAdapter()
    system_data = adapter.get_system_data(527609567169)
    physical_body_subsystems, barycentre_subsystems = adapter._group_system_subsystems(system_data)
    construction_order = adapter._get_subsystem_construction_order(physical_body_subsystems, barycentre_subsystems)
    pprint(adapter._process_construction_order(system_data, construction_order))