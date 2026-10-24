import rebound
import math
from pprint import pprint
from caspian_surveyor.rebound.caspian_rebound_mappings import CaspianReboundMappings, Rebound, ReboundBarycentre

AU_IN_METERS = 149_597_870_700


class ReboundAdapter:

    def __init__(self) -> None:
        self.simulation = rebound.Simulation()
        self.simulation.units = ("AU", "yr", "Msun")
        self.mapping = CaspianReboundMappings()
        self.rebound_bodies_dict = self.mapping.build_rebound_bodies_dict()
        self.rebound_barycentres_dict = self.mapping.build_rebound_barycentres_dict()
        self.processed_barycentres: set[int] = set()


    def add_primary_star_to_simulation(self,
            name: str,
            mass: float,
        ):

        self.particle = rebound.Particle()

        self.particle.name=name
        self.particle.m=mass

        self.simulation.add(self.particle)

        return self.particle

    def process_rebound_data(self):
        rebound_dict = self.mapping.build_rebound_bodies_dict()
        rebound_barycentres = self.mapping.build_rebound_barycentres_dict()
        self.add_primary_star_to_simulation(
            name="Ovoks QT-P d6-1",
            mass=1.539063
        )

        sorted_rebound = dict(
            sorted(rebound_dict.items(), key=lambda item: item[1].body_id)
        )

        for rebound_obj in sorted_rebound.values():
            if rebound_obj.body_mass == 0:
                continue

            if rebound_obj.body_mass is None:
                continue

            if rebound_obj.body_parents == []:
                continue

            parent = self.mapping.resolve_immediate_parent(
                rebound_obj.body_parents,
                sorted_rebound,
                rebound_barycentres
            )

            assert parent is not None

            print("Body ID", rebound_obj.body_id)
            print("Body Name", rebound_obj.body_name)
            print("Parent ID", parent.body_id)
            print("============================\n")


            if isinstance(parent, ReboundBarycentre):

                if parent.body_id in self.processed_barycentres:
                    continue

                self.add_barycentric_subsystem_to_simulation(
                    barycentre=parent,
                    rebound_bodies=sorted_rebound,
                )

                self.processed_barycentres.add(parent.body_id)

                continue
            else:
                self.simulation.add(
                    name=rebound_obj.body_name,
                    primary=parent.body_name,
                    m=rebound_obj.body_mass,
                    omega=math.radians(rebound_obj.body_periapsis),
                    a=rebound_obj.body_semi_major_axis / AU_IN_METERS,
                    e=rebound_obj.body_eccentricity,
                    inc=math.radians(rebound_obj.body_orbital_inclination),
                    Omega=math.radians(rebound_obj.body_ascending_node),
                    M=math.radians(rebound_obj.body_mean_anomaly)
                )         


    def add_barycentric_subsystem_to_simulation(
            self,
            barycentre: ReboundBarycentre,
            rebound_bodies: dict[int, Rebound],
        ):

        barycentre_children = []

        for rebound_body in rebound_bodies.values():

            if not rebound_body.body_parents:
                continue

            immediate_parent = rebound_body.body_parents[0]

            if (
                immediate_parent.parent_type == "Null"
                and immediate_parent.parent_body_id == barycentre.body_id
            ):
                barycentre_children.append(rebound_body)

        if len(barycentre_children) != 2:
            raise ValueError(
                f"Barycentre {barycentre.body_id} expected 2 physical children, "
                f"found {len(barycentre_children)}."
            )

        barycentre_parent_map = (
            self.mapping.infer_barycentre_immediate_parents(
                rebound_bodies
            )
        )

        barycentre_parent_info = barycentre_parent_map[barycentre.body_id]

        if barycentre_parent_info.parent_type == "Null":
            raise NotImplementedError(
                "Nested barycentre parents are not implemented yet."
            )

        barycentre_parent = rebound_bodies[
            barycentre_parent_info.parent_body_id
        ]

        simulation_parent = self.simulation.particles[
            barycentre_parent.body_name
        ]

        child_one = barycentre_children[0]
        child_two = barycentre_children[1]

        subsystem_mass = (
            child_one.body_mass
            + child_two.body_mass
        )

        if barycentre.semi_major_axis is None:
            raise ValueError("Barycentre semi-major axis is missing.")

        if barycentre.eccentricity is None:
            raise ValueError("Barycentre eccentricity is missing.")

        if barycentre.orbital_inclination is None:
            raise ValueError("Barycentre orbital inclination is missing.")

        if barycentre.periapsis is None:
            raise ValueError("Barycentre periapsis is missing.")

        if barycentre.ascending_node is None:
            raise ValueError("Barycentre ascending node is missing.")

        if barycentre.mean_anomaly is None:
            raise ValueError("Barycentre mean anomaly is missing.")

        barycentre_particle = rebound.Particle(
            simulation=self.simulation,
            primary=simulation_parent,
            m=subsystem_mass,
            a=barycentre.semi_major_axis / AU_IN_METERS,
            e=barycentre.eccentricity,
            inc=math.radians(
                barycentre.orbital_inclination
            ),
            Omega=math.radians(
                barycentre.ascending_node
            ),
            omega=math.radians(
                barycentre.periapsis
            ),
            M=math.radians(
                barycentre.mean_anomaly
            ),
        )

        binary_simulation = rebound.Simulation()
        binary_simulation.units = ("AU", "yr", "Msun")

        if child_one.body_mass >= child_two.body_mass:
            binary_primary = child_one
            binary_secondary = child_two
        else:
            binary_primary = child_two
            binary_secondary = child_one

        if binary_primary.body_semi_major_axis is None:
            raise ValueError("Binary primary semi-major axis is missing.")

        if binary_secondary.body_semi_major_axis is None:
            raise ValueError("Binary secondary semi-major axis is missing.")


        # testing calculations

        relative_semi_major_axis = (
            binary_primary.body_semi_major_axis
            + binary_secondary.body_semi_major_axis
        ) / AU_IN_METERS

        binary_simulation.add(
            name=binary_primary.body_name,
            m=binary_primary.body_mass,
        )

        binary_primary_particle = (
            binary_simulation.particles[
                binary_primary.body_name
            ]
        )

        binary_simulation.add(
            name=binary_secondary.body_name,
            primary=binary_primary_particle,
            m=binary_secondary.body_mass,
            a=relative_semi_major_axis,
            e=binary_secondary.body_eccentricity,
            inc=math.radians(
                binary_secondary.body_orbital_inclination
            ),
            Omega=math.radians(
                binary_secondary.body_ascending_node
            ),
            omega=math.radians(
                binary_secondary.body_periapsis
            ),
            M=math.radians(
                binary_secondary.body_mean_anomaly
            ),
        )

        binary_simulation.move_to_com()

        local_primary = binary_simulation.particles[
            binary_primary.body_name
        ]

        local_secondary = binary_simulation.particles[
            binary_secondary.body_name
        ]

        self.simulation.add(
            name=binary_primary.body_name,
            m=binary_primary.body_mass,

            x=local_primary.x + barycentre_particle.x,
            y=local_primary.y + barycentre_particle.y,
            z=local_primary.z + barycentre_particle.z,

            vx=local_primary.vx + barycentre_particle.vx,
            vy=local_primary.vy + barycentre_particle.vy,
            vz=local_primary.vz + barycentre_particle.vz,
        )

        self.simulation.add(
            name=binary_secondary.body_name,
            m=binary_secondary.body_mass,

            x=local_secondary.x + barycentre_particle.x,
            y=local_secondary.y + barycentre_particle.y,
            z=local_secondary.z + barycentre_particle.z,

            vx=local_secondary.vx + barycentre_particle.vx,
            vy=local_secondary.vy + barycentre_particle.vy,
            vz=local_secondary.vz + barycentre_particle.vz,
        )

        print(
            f"Added barycentric subsystem {barycentre.body_id}: "
            f"{binary_primary.body_id}, {binary_secondary.body_id}"
        )

        print(f"Simulation Bodies: {self.simulation.N}")

        particle_one = self.simulation.particles[
            binary_primary.body_name
        ]

        particle_two = self.simulation.particles[
            binary_secondary.body_name
        ]


        combined_mass = particle_one.m + particle_two.m

        calculated_com_x = (
            (particle_one.m * particle_one.x)
            + (particle_two.m * particle_two.x)
        ) / combined_mass

        calculated_com_y = (
            (particle_one.m * particle_one.y)
            + (particle_two.m * particle_two.y)
        ) / combined_mass

        calculated_com_z = (
            (particle_one.m * particle_one.z)
            + (particle_two.m * particle_two.z)
        ) / combined_mass

        calculated_com_vx = (
            (particle_one.m * particle_one.vx)
            + (particle_two.m * particle_two.vx)
        ) / combined_mass

        calculated_com_vy = (
            (particle_one.m * particle_one.vy)
            + (particle_two.m * particle_two.vy)
        ) / combined_mass

        calculated_com_vz = (
            (particle_one.m * particle_one.vz)
            + (particle_two.m * particle_two.vz)
        ) / combined_mass



        print("EXPECTED BARYCENTRE")
        print(
            barycentre_particle.x,
            barycentre_particle.y,
            barycentre_particle.z
        )

        print("CALCULATED COM")
        print(
            calculated_com_x,
            calculated_com_y,
            calculated_com_z
        )

        print("EXPECTED BARYCENTRE VELOCITY")
        print(
            barycentre_particle.vx,
            barycentre_particle.vy,
            barycentre_particle.vz
        )

        print("CALCULATED COM VELOCITY")
        print(
            calculated_com_vx,
            calculated_com_vy,
            calculated_com_vz
        )

        particle_primary = self.simulation.particles[
            binary_primary.body_name
        ]

        particle_secondary = self.simulation.particles[
            binary_secondary.body_name
        ]

        relative_orbit = particle_secondary.orbit(
            primary=particle_primary
        )

        expected_relative_a = (
            binary_primary.body_semi_major_axis
            + binary_secondary.body_semi_major_axis
        ) / AU_IN_METERS

        calculated_primary_a = (
            relative_orbit.a
            * particle_secondary.m
            / combined_mass
        )

        calculated_secondary_a = (
            relative_orbit.a
            * particle_primary.m
            / combined_mass
        )

        print("RELATIVE SEMI-MAJOR AXIS")
        print("Elite implied:", expected_relative_a)
        print("REBOUND:", relative_orbit.a)

        print("ECCENTRICITY")
        print("Elite:", binary_secondary.body_eccentricity)
        print("REBOUND:", relative_orbit.e)

        print("INCLINATION")
        print(
            "Elite:",
            math.radians(binary_secondary.body_orbital_inclination)
        )
        print("REBOUND:", relative_orbit.inc)

        print("ASCENDING NODE")
        print(
            "Elite:",
            math.radians(binary_secondary.body_ascending_node)
        )
        print("REBOUND:", relative_orbit.Omega)

        print("PERIAPSIS")
        print(
            "Elite:",
            math.radians(binary_secondary.body_periapsis)
        )
        print("REBOUND:", relative_orbit.omega)

        print("MEAN ANOMALY")
        print(
            "Elite:",
            math.radians(binary_secondary.body_mean_anomaly)
        )
        print("REBOUND:", relative_orbit.M)

        print("PRIMARY BARYCENTRIC A")
        print(
            "Elite:",
            binary_primary.body_semi_major_axis / AU_IN_METERS
        )
        print(
            "REBOUND derived:",
            calculated_primary_a
        )

        print("SECONDARY BARYCENTRIC A")
        print(
            "Elite:",
            binary_secondary.body_semi_major_axis / AU_IN_METERS
        )
        print(
            "REBOUND derived:",
            calculated_secondary_a
        )





if __name__ == '__main__':
    adapter = ReboundAdapter()

    adapter.process_rebound_data()

    print("=======================================")

    for rebound_body in adapter.rebound_bodies_dict.values():

        if not rebound_body.body_parents:
            continue

        parent = adapter.mapping.resolve_immediate_parent(
            rebound_body.body_parents,
            adapter.rebound_bodies_dict,
            adapter.rebound_barycentres_dict
        )

        if isinstance(parent, ReboundBarycentre):
            continue

        particle = adapter.simulation.particles[
            rebound_body.body_name
        ]

        primary_particle = adapter.simulation.particles[
            parent.body_name
        ]

        orbit = particle.orbit(
            primary=primary_particle
        )

        print(
            rebound_body.body_name,
            orbit.a,
            orbit.e,
            orbit.inc,
            orbit.Omega,
            orbit.omega,
            orbit.M
        )

    print("=======================================")

    for each_body in adapter.simulation.particles[1:]:
        print(each_body.name, each_body.orbit(primary=adapter.simulation.particles[0]))


    # adapter.simulation.particles[1].orbit(primary=adapter.simulation.particles[0])

    
    # adapter.simulation.start_server(port=1234)

    # # Value is microseconds.
    # adapter.simulation.usleep = 6000

    # print("Simulation running indefinitely.")
    # print("Open http://localhost:1234")
    # print("CTRL+C to stop.")

    # try:
    #     adapter.simulation.integrate(float("inf"))

    # except KeyboardInterrupt:
    #     print("\nSimulation stopped.")

    # finally:
    #     adapter.simulation.stop_server()