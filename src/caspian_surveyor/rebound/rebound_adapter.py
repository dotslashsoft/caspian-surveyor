import rebound
import logging
from pprint import pprint
from caspian_surveyor.rebound.caspian_to_rebound_data_prep import CaspianDataHandler
from typing import Any
import math

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
                            resolved_barycentre_subsystems,
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
            resolved_physical_subsystems: dict,
            resolved_barycentre_subsystems: dict
    ):
        temp_sim = rebound.Simulation()
        temp_sim.units = ("AU", "yr", "Msun")

        primary_body = system_data[parent_id]

        physical_child_ids = []
        barycentre_child_ids = []
        incorporated_body_ids = []

        for child_id in child_ids:

            if system_data[child_id]["type"] == "body":
                physical_child_ids.append(child_id)
            else:
                barycentre_child_ids.append(child_id)

        self._add_primary_physical_body(primary_body, temp_sim)

        for child_id in physical_child_ids:

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
                primary=temp_sim.particles[0],
            )

        for child_id in physical_child_ids:

            if child_id in resolved_physical_subsystems:

                added_body_ids = self._incorporate_physical_subsystem(
                    child_id,
                    resolved_physical_subsystems,
                    temp_sim,
                )

                incorporated_body_ids.extend(added_body_ids)

        for barycentre_id in barycentre_child_ids:

            added_body_ids = self._incorporate_barycentric_subsystem(
                system_data,
                barycentre_id,
                parent_id,
                resolved_barycentre_subsystems,
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
        barycentre_child_ids = []
        incorporated_body_ids = []

        for child_id in child_ids:

            if system_data[child_id]["type"] == "body":
                physical_child_ids.append(child_id)

            else:
                barycentre_child_ids.append(child_id)

        if not physical_child_ids:
            raise ValueError(
                f"Barycentre {parent_id} has no direct physical "
                "children available for construction."
            )

        orbital_match_fields = (
            "eccentricity",
            "orbital_inclination",
            "ascending_node",
            "mean_anomaly",
        )

        # construct the direct physical children
        if len(child_ids) == 2 and len(physical_child_ids) == 2:

            first_id, second_id = physical_child_ids

            first_body = system_data[first_id]
            second_body = system_data[second_id]

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

        else:

            primary_body_id = physical_child_ids[0]
            primary_body = system_data[primary_body_id]

            self._add_primary_physical_body(primary_body, temp_sim)

            binary_primary = None

            for body_id in physical_child_ids[1:]:

                child_body = system_data[body_id]

                semi_major_axis = child_body["semi_major_axis"]

                matching_orbital_elements = all(
                    abs(primary_body[field] - child_body[field]) < 1e-6
                    for field in orbital_match_fields
                )

                periapsis_difference = (
                    primary_body["periapsis"]
                    - child_body["periapsis"]
                ) % (2 * math.pi)

                opposite_periapsis = (
                    abs(periapsis_difference - math.pi)
                    < math.radians(0.001)
                )

                first_moment = (
                    primary_body["mass"]
                    * primary_body["semi_major_axis"]
                )

                second_moment = (
                    child_body["mass"]
                    * child_body["semi_major_axis"]
                )

                maximum_moment = max(first_moment, second_moment)

                mass_axis_difference = (
                    abs(first_moment - second_moment) / maximum_moment
                    if maximum_moment > 0
                    else float("inf")
                )

                is_binary_companion = (
                    matching_orbital_elements
                    and opposite_periapsis
                    and mass_axis_difference < 0.001
                )

                if is_binary_companion:
                    semi_major_axis += primary_body["semi_major_axis"]

                temp_sim.add(
                    m=child_body["mass"],
                    a=semi_major_axis,
                    e=child_body["eccentricity"],
                    inc=child_body["orbital_inclination"],
                    Omega=child_body["ascending_node"],
                    omega=child_body["periapsis"],
                    M=child_body["mean_anomaly"],
                    name=child_body["name"],
                    primary=(
                        binary_primary
                        if binary_primary is not None
                        else temp_sim.particles[0]
                    ),
                )

                # establish the binary COM for subsequent bodies
                if is_binary_companion:

                    first_particle = temp_sim.particles[
                        primary_body["name"]
                    ]

                    second_particle = temp_sim.particles[
                        child_body["name"]
                    ]

                    total_mass = first_particle.m + second_particle.m

                    coordinates = ("x", "y", "z", "vx", "vy", "vz")

                    binary_primary = rebound.Particle(
                        m=total_mass,
                        **{
                            coordinate: (
                                first_particle.m
                                * getattr(first_particle, coordinate)
                                + second_particle.m
                                * getattr(second_particle, coordinate)
                            ) / total_mass
                            for coordinate in coordinates
                        },
                    )

        # incorporate previously constructed physical subsystems
        for child_id in physical_child_ids:

            if child_id in resolved_physical_subsystems:

                added_body_ids = self._incorporate_physical_subsystem(
                    child_id,
                    resolved_physical_subsystems,
                    temp_sim,
                )

                incorporated_body_ids.extend(added_body_ids)

        # detect candidate physical binary pairs
        candidate_binary_pairs = []

        for index, first_id in enumerate(physical_child_ids):

            for second_id in physical_child_ids[index + 1:]:

                first_body = system_data[first_id]
                second_body = system_data[second_id]

                if not all(
                    abs(first_body[field] - second_body[field]) < 1e-6
                    for field in orbital_match_fields
                ):
                    continue

                periapsis_difference = (
                    first_body["periapsis"]
                    - second_body["periapsis"]
                ) % (2 * math.pi)

                if abs(periapsis_difference - math.pi) > math.radians(0.001):
                    continue

                first_moment = (
                    first_body["mass"] * first_body["semi_major_axis"]
                )

                second_moment = (
                    second_body["mass"] * second_body["semi_major_axis"]
                )

                maximum_moment = max(first_moment, second_moment)

                if maximum_moment <= 0:
                    continue

                relative_difference = (
                    abs(first_moment - second_moment) / maximum_moment
                )

                print(
                    f"Parent barycentre {parent_id}: "
                    f"candidate physical binary ({first_id}, {second_id}), "
                    f"mass-axis difference = {relative_difference:.6%}"
                )

                if relative_difference >= 0.001:
                    continue

                candidate_binary_pairs.append((first_id, second_id))

                first_particle = temp_sim.particles[first_body["name"]]
                second_particle = temp_sim.particles[second_body["name"]]

                expected_relative_a = (
                    first_body["semi_major_axis"]
                    + second_body["semi_major_axis"]
                )

                actual_relative_a = second_particle.orbit(
                    primary=first_particle
                ).a

                print(
                    f"Binary ({first_id}, {second_id}): "
                    f"expected a = {expected_relative_a:.9f} AU, "
                    f"actual a = {actual_relative_a:.9f} AU"
                )

        # incorporate previously constructed barycentric subsystems
        for barycentre_id in barycentre_child_ids:

            barycentre_data = system_data[barycentre_id]

            matching_physical_ids = []

            for physical_id in physical_child_ids:

                physical_data = system_data[physical_id]

                if all(
                    abs(barycentre_data[field] - physical_data[field]) < 1e-6
                    for field in orbital_match_fields
                ):
                    matching_physical_ids.append(physical_id)

            print(
                f"Barycentre {barycentre_id} under parent {parent_id}: "
                f"matching physical siblings = {matching_physical_ids}"
            )

            incorporated = False

            # Case 1: a matching physical binary companion exists
            for physical_id in matching_physical_ids:

                physical_data = system_data[physical_id]

                periapsis_difference = (
                    barycentre_data["periapsis"]
                    - physical_data["periapsis"]
                ) % (2 * math.pi)

                print(
                    f"Orbital pair {barycentre_id} and {physical_id}: "
                    f"periapsis difference = "
                    f"{math.degrees(periapsis_difference):.6f}°"
                )

                barycentre_mass = sum(
                    particle["mass"]
                    for particle in resolved_barycentre_subsystems[
                        barycentre_id
                    ]["particles"].values()
                )

                barycentre_moment = (
                    barycentre_mass
                    * barycentre_data["semi_major_axis"]
                )

                physical_moment = (
                    physical_data["mass"]
                    * physical_data["semi_major_axis"]
                )

                maximum_moment = max(
                    barycentre_moment,
                    physical_moment,
                )

                relative_difference = (
                    abs(barycentre_moment - physical_moment)
                    / maximum_moment
                    if maximum_moment > 0
                    else float("inf")
                )

                print(
                    f"Orbital pair {barycentre_id} and {physical_id}: "
                    f"mass-axis difference = {relative_difference:.6%}"
                )

                if (
                    abs(periapsis_difference - math.pi)
                    > math.radians(0.001)
                    or relative_difference > 0.001
                ):
                    continue

                relative_a = (
                    barycentre_data["semi_major_axis"]
                    + physical_data["semi_major_axis"]
                )

                primary_particle = temp_sim.particles[
                    physical_data["name"]
                ]

                added_body_ids = self._incorporate_barycentric_subsystem(
                    system_data=system_data,
                    barycentre_id=barycentre_id,
                    physical_parent_id=None,
                    resolved_barycentre_subsystems=resolved_barycentre_subsystems,
                    temp_sim=temp_sim,
                    primary_particle=primary_particle,
                    relative_semi_major_axis=relative_a,
                )

                incorporated_body_ids.extend(added_body_ids)
                incorporated = True

                # DIAGNOSTIC: combined COM of the paired components
                # run only after incorporating the barycentric subsystem
                component_ids = [
                    physical_id,
                    *resolved_barycentre_subsystems[barycentre_id]["particles"],
                ]

                component_particles = [
                    temp_sim.particles[system_data[body_id]["name"]]
                    for body_id in component_ids
                ]

                total_mass = sum(
                    particle.m for particle in component_particles
                )

                coordinates = ("x", "y", "z", "vx", "vy", "vz")

                combined_com = rebound.Particle(
                    m=total_mass,
                    **{
                        coordinate: sum(
                            particle.m * getattr(particle, coordinate)
                            for particle in component_particles
                        ) / total_mass
                        for coordinate in coordinates
                    },
                )

                # reposition direct circumbinary bodies relative to
                # the combined barycentric center of mass
                for child_id in physical_child_ids:

                    if child_id == physical_id:
                        continue

                    child_data = system_data[child_id]

                    child_particle = temp_sim.particles[
                        child_data["name"]
                    ]

                    # calculate the correct orbital state without
                    # adding another particle to the simulation
                    target_particle = rebound.Particle(
                        simulation=temp_sim,
                        primary=combined_com,
                        m=child_data["mass"],
                        a=child_data["semi_major_axis"],
                        e=child_data["eccentricity"],
                        inc=child_data["orbital_inclination"],
                        Omega=child_data["ascending_node"],
                        omega=child_data["periapsis"],
                        M=child_data["mean_anomaly"],
                    )

                    # calculate the position and velocity translation
                    translation = {
                        coordinate: (
                            getattr(target_particle, coordinate)
                            - getattr(child_particle, coordinate)
                        )
                        for coordinate in coordinates
                    }

                    # include any previously incorporated descendants
                    bodies_to_move = [child_id]

                    if child_id in resolved_physical_subsystems:

                        bodies_to_move.extend(
                            body_id
                            for body_id in resolved_physical_subsystems[
                                child_id
                            ]["particles"]
                            if body_id != child_id
                        )

                    # apply the same Cartesian translation to every
                    # physical body in this subtree
                    for body_id in bodies_to_move:

                        particle = temp_sim.particles[
                            system_data[body_id]["name"]
                        ]

                        for coordinate in coordinates:
                            setattr(
                                particle,
                                coordinate,
                                getattr(particle, coordinate)
                                + translation[coordinate],
                            )

                    actual_a = child_particle.orbit(
                        primary=combined_com
                    ).a

                    print(
                        f"Barycentre {parent_id}, body {child_id}: "
                        f"expected a = "
                        f"{child_data['semi_major_axis']:.9f} AU, "
                        f"actual a = {actual_a:.9f} AU"
                    )

                break

            if incorporated:
                continue

            # Case 2: use an identified physical binary's COM
            if len(candidate_binary_pairs) != 1:
                raise ValueError(
                    f"Unable to identify a unique binary reference "
                    f"for barycentre {barycentre_id}."
                )

            first_id, second_id = candidate_binary_pairs[0]

            first_particle = temp_sim.particles[
                system_data[first_id]["name"]
            ]

            second_particle = temp_sim.particles[
                system_data[second_id]["name"]
            ]

            total_mass = first_particle.m + second_particle.m

            coordinates = ("x", "y", "z", "vx", "vy", "vz")

            binary_com = rebound.Particle(
                m=total_mass,
                **{
                    coordinate: (
                        first_particle.m * getattr(first_particle, coordinate)
                        + second_particle.m * getattr(second_particle, coordinate)
                    ) / total_mass
                    for coordinate in coordinates
                },
            )

            added_body_ids = self._incorporate_barycentric_subsystem(
                system_data=system_data,
                barycentre_id=barycentre_id,
                physical_parent_id=None,
                resolved_barycentre_subsystems=resolved_barycentre_subsystems,
                temp_sim=temp_sim,
                primary_particle=binary_com,
            )

            incorporated_body_ids.extend(added_body_ids)

        # DIAGNOSTIC: verify direct circumbinary physical children
        for first_id, second_id in candidate_binary_pairs:

            first_particle = temp_sim.particles[
                system_data[first_id]["name"]
            ]

            second_particle = temp_sim.particles[
                system_data[second_id]["name"]
            ]

            total_mass = first_particle.m + second_particle.m

            coordinates = ("x", "y", "z", "vx", "vy", "vz")

            binary_com = rebound.Particle(
                m=total_mass,
                **{
                    coordinate: (
                        first_particle.m * getattr(first_particle, coordinate)
                        + second_particle.m * getattr(second_particle, coordinate)
                    ) / total_mass
                    for coordinate in coordinates
                },
            )

            for child_id in physical_child_ids:

                if child_id in (first_id, second_id):
                    continue

                child_data = system_data[child_id]

                child_particle = temp_sim.particles[
                    child_data["name"]
                ]

                expected_a = child_data["semi_major_axis"]

                actual_a = child_particle.orbit(
                    primary=binary_com
                ).a

                print(
                    f"Circumbinary body {child_id}: "
                    f"expected a = {expected_a:.9f} AU, "
                    f"actual a = {actual_a:.9f} AU"
                )

        # DIAGNOSTIC: verify the completed root particle count
        if system_data[parent_id]["immediate_parent"] is None:
            print(f"Root simulation particles: {temp_sim.N}")

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

    def _incorporate_barycentric_subsystem(
            self,
            system_data: dict,
            barycentre_id: int,
            physical_parent_id: int | None,
            resolved_barycentre_subsystems: dict,
            temp_sim,
            primary_particle=None,
            relative_semi_major_axis: float | None = None
    ) -> list[int]:

        barycentre_data = system_data[barycentre_id]
        resolved_subsystem = resolved_barycentre_subsystems[barycentre_id]
        subsystem_particles = resolved_subsystem["particles"]

        coordinates = ("x", "y", "z", "vx", "vy", "vz")

        total_mass = sum(
            particle["mass"]
            for particle in subsystem_particles.values()
        )

        if total_mass <= 0:
            raise ValueError(
                f"Barycentre {barycentre_id} has no positive physical mass."
            )

        local_com = {
            coordinate: sum(
                particle["mass"] * particle[coordinate]
                for particle in subsystem_particles.values()
            ) / total_mass
            for coordinate in coordinates
        }

        if primary_particle is None:
            parent_name = system_data[physical_parent_id]["name"]
            primary_particle = temp_sim.particles[parent_name]

        if relative_semi_major_axis is None:
            semi_major_axis = barycentre_data["semi_major_axis"]
        else:
            semi_major_axis = relative_semi_major_axis

        barycentre_com = rebound.Particle(
            simulation=temp_sim,
            primary=primary_particle,
            m=total_mass,
            a=semi_major_axis,
            e=barycentre_data["eccentricity"],
            inc=barycentre_data["orbital_inclination"],
            Omega=barycentre_data["ascending_node"],
            omega=barycentre_data["periapsis"],
            M=barycentre_data["mean_anomaly"],
        )

        target_com = {
            coordinate: getattr(barycentre_com, coordinate)
            for coordinate in coordinates
        }

        incorporated_body_ids = []

        for body_id, body_data in subsystem_particles.items():

            translated_state = {
                coordinate: (
                    target_com[coordinate]
                    + body_data[coordinate]
                    - local_com[coordinate]
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
    system_data = adapter.get_system_data(527609567169)
    # system_data = adapter.get_system_data(38562352187)

    physical_body_subsystems, barycentre_subsystems = adapter._group_system_subsystems(system_data)

    construction_order = adapter._get_subsystem_construction_order(physical_body_subsystems, barycentre_subsystems)
    resolved_barycentre_subsystems, resolved_physical_subsystems = adapter._process_construction_order(system_data, construction_order)

    source = resolved_physical_subsystems[33]["particles"]
    destination = resolved_barycentre_subsystems[2]["particles"]

    coordinates = ("x", "y", "z", "vx", "vy", "vz")

    for coordinate in coordinates:

        original = (
            source[34][coordinate]
            - source[33][coordinate]
        )

        translated = (
            destination[34][coordinate]
            - destination[33][coordinate]
        )

        print(
            f"{coordinate}: "
            f"difference = {abs(original - translated):.12e}"
        )