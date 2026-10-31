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

    def _process_construction_order(
            self,
            system_data: dict,
            construction_order: list
    ):
        resolved_barycentre_subsystems = {}
        resolved_physical_subsystems = {}

        for stage in construction_order:
            for parent_id in stage:

                child_ids = system_data[parent_id]["immediate_children"]

                if system_data[parent_id]["type"] == "barycentre":
                    resolved_barycentre_subsystem = {
                        "barycentre_id": parent_id,
                        "particles": {},
                    }

                    temp_sim, incorporated_body_ids = (
                        self._construct_barycentre_subsystem(
                            system_data,
                            parent_id,
                            child_ids,
                            resolved_barycentre_subsystems,
                            resolved_physical_subsystems,
                        )
                    )

                    stored_body_ids = [
                        *child_ids,
                        *incorporated_body_ids,
                    ]

                    self._store_temp_sim_data(
                        system_data,
                        stored_body_ids,
                        resolved_barycentre_subsystem,
                        temp_sim,
                    )

                    resolved_barycentre_subsystems[parent_id] = (
                        resolved_barycentre_subsystem
                    )

                else:
                    physical_body_id = parent_id
                    physical_body_children = system_data[
                        physical_body_id
                    ]["immediate_children"]

                    resolved_physical_subsystem = {
                        "parent_body_id": physical_body_id,
                        "particles": {},
                    }

                    temp_sim, incorporated_body_ids = (
                        self._construct_physical_body_subsystem(
                            system_data,
                            physical_body_id,
                            physical_body_children,
                            resolved_physical_subsystems,
                        )
                    )

                    stored_body_ids = [
                        physical_body_id,
                        *physical_body_children,
                        *incorporated_body_ids,
                    ]

                    self._store_temp_sim_data(
                        system_data,
                        stored_body_ids,
                        resolved_physical_subsystem,
                        temp_sim,
                    )

                    resolved_physical_subsystems[physical_body_id] = (
                        resolved_physical_subsystem
                    )

        return resolved_barycentre_subsystems, resolved_physical_subsystems

    def _construct_physical_body_subsystem(
            self,
            system_data: dict,
            parent_id,
            child_ids: list,
            resolved_physical_subsystems: dict
    ):
        temp_sim = rebound.Simulation()
        temp_sim.units = ("AU", "yr", "Msun")

        primary_body = system_data[parent_id]
        physical_child_list = []
        incorporated_body_ids = []

        for child_id in child_ids:
            if system_data[child_id]["type"] == "body":
                physical_child_list.append(child_id)
            else:
                print(f"Skipping resolved barycentre {child_id} for now.")

        self._add_primary_physical_body(primary_body, temp_sim)

        primary = temp_sim.particles[0]

        for child_id in physical_child_list:
            child_body = system_data[child_id]

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

        # Incorporate previously constructed physical subsystems.
        for child_id in physical_child_list:
            if child_id in resolved_physical_subsystems:

                added_body_ids = self._incorporate_physical_subsystem(
                    child_id,
                    resolved_physical_subsystems,
                    temp_sim,
                )

                incorporated_body_ids.extend(added_body_ids)

        return temp_sim, incorporated_body_ids

    def _construct_barycentre_subsystem(
            self,
            system_data: dict,
            parent_id,
            child_ids: list,
            resolved_barycentre_subsystems: dict,
            resolved_physical_subsystems: dict
    ):
        temp_sim = rebound.Simulation()
        temp_sim.units = ("AU", "yr", "Msun")

        physical_child_ids = []
        incorporated_body_ids = []
        # Identify physical children.
        for child_id in child_ids:

            if system_data[child_id]["type"] == "body":
                physical_child_ids.append(child_id)

            else:
                # Barycentric incorporation is not implemented yet.
                # These subsystems are already constructed,
                # but are not currently inserted here.
                continue

        if not physical_child_ids:
            raise ValueError(
                f"Barycentre {parent_id} has no direct physical "
                "children available for construction."
            )
        # Construct a binary subsystem containing two physical bodies.
        if len(child_ids) == 2 and len(physical_child_ids) == 2:

            first_body_id, second_body_id = physical_child_ids

            first_body = system_data[first_body_id]
            second_body = system_data[second_body_id]

            self._add_primary_physical_body(first_body, temp_sim)

            relative_a = (
                first_body["semi_major_axis"]
                + second_body["semi_major_axis"]
            )

            temp_sim.add(
                m=second_body["mass"],
                a=relative_a,
                e=second_body["eccentricity"],
                inc=second_body["orbital_inclination"],
                Omega=second_body["ascending_node"],
                omega=second_body["periapsis"],
                M=second_body["mean_anomaly"],
                name=second_body["name"],
                primary=temp_sim.particles[0],
            )
        # Construct the available direct physical children.
        else:

            primary_body_id = physical_child_ids[0]
            primary_body = system_data[primary_body_id]

            self._add_primary_physical_body(primary_body, temp_sim)

            orbiting_body_ids = physical_child_ids[1:]

            for body_id in orbiting_body_ids:

                child_body = system_data[body_id]

                temp_sim.add(
                    m=child_body["mass"],
                    a=child_body["semi_major_axis"],
                    e=child_body["eccentricity"],
                    inc=child_body["orbital_inclination"],
                    Omega=child_body["ascending_node"],
                    omega=child_body["periapsis"],
                    M=child_body["mean_anomaly"],
                    name=child_body["name"],
                    primary=temp_sim.particles[0],
                )
        # Incorporate previously constructed physical subsystems.
        for child_id in physical_child_ids:

            if child_id in resolved_physical_subsystems:

                added_body_ids = self._incorporate_physical_subsystem(
                    child_id,
                    resolved_physical_subsystems,
                    temp_sim,
                )

                incorporated_body_ids.extend(added_body_ids)
        # Center the assembled particles.
        temp_sim.move_to_com()

        return temp_sim, incorporated_body_ids

    def _incorporate_physical_subsystem(
            self,
            parent_body_id: int,
            resolved_physical_subsystems: dict,
            temp_sim
    ) -> list[int]:
        resolved_subsystem = resolved_physical_subsystems[parent_body_id]
        subsystem_particles = resolved_subsystem["particles"]

        local_parent = subsystem_particles[parent_body_id]
        parent_particle = temp_sim.particles[local_parent["name"]]

        coordinates = ("x", "y", "z", "vx", "vy", "vz")

        parent_state = {
            coordinate: getattr(parent_particle, coordinate)
            for coordinate in coordinates
        }

        incorporated_body_ids = []

        for body_id, body_data in subsystem_particles.items():
            if body_id == parent_body_id:
                continue

            translated_state = {
                coordinate: (
                    parent_state[coordinate]
                    + body_data[coordinate]
                    - local_parent[coordinate]
                )
                for coordinate in coordinates
            }

            temp_sim.add(
                m=body_data["mass"],
                name=body_data["name"],
                **translated_state,
            )

            incorporated_body_ids.append(body_id)

        return incorporated_body_ids

    def _add_primary_physical_body(self, primary_physical_body, temp_sim):
        temp_sim.add(
            m=primary_physical_body["mass"],
            name=str(primary_physical_body["name"])
        )

    def _store_temp_sim_data(
            self,
            system_data: dict,
            child_ids: list,
            resolved_subsystem: dict,
            temp_sim
    ):
        for child_id in child_ids:
            if system_data[child_id]["type"] == "barycentre":
                continue

            child_name = system_data[child_id]["name"]
            particle = temp_sim.particles[child_name]

            resolved_subsystem["particles"][child_id] = {
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
    # system_data = adapter.get_system_data(527609567169)
    system_data = adapter.get_system_data(38562352187)
    physical_body_subsystems, barycentre_subsystems = adapter._group_system_subsystems(system_data)

    construction_order = adapter._get_subsystem_construction_order(physical_body_subsystems, barycentre_subsystems)
    resolved_barycentre_subsystems, resolved_physical_subsystems = adapter._process_construction_order(system_data, construction_order)

    pprint(resolved_barycentre_subsystems, sort_dicts=False)
    pprint(resolved_physical_subsystems, sort_dicts=False)