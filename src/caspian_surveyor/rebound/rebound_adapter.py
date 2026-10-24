import rebound
import math
from pprint import pprint
from caspian_surveyor.rebound.caspian_rebound_mappings import CaspianReboundMappings, Rebound, ReboundBarycentre

# sim = rebound.Simulation()
# sim.units = ("AU", "yr", "Msun")


class ReboundAdapter:

    def __init__(self) -> None:
        self.simulation = rebound.Simulation()
        self.simulation.units = ("AU", "yr", "Msun")
        self.mapping = CaspianReboundMappings()
        self.rebound_bodies_dict = self.mapping.build_rebound_bodies_dict()
        self.rebound_barycentres_dict = self.mapping.build_rebound_barycentres_dict()


    def add_primary_star_to_simulation(self, name: str, mass: float):
        particle = rebound.Particle()
        particle.name=name
        # m=mass
        particle.m=mass
        self.simulation.add(particle)
        print(self.simulation.N)
        print(self.simulation.particles[0])


    def add_body_to_simulation(self, name, primary, mass):
        pass


if __name__ == '__main__':
    adapter = ReboundAdapter()

    adapter.add_primary_star_to_simulation("Sol", 1.4)



# Elite Dangerous journal     Caspian DB             REBOUND
# ----------------------------------------------------------------
# SemiMajorAxis               semi_major_axis        a
# Eccentricity                eccentricity           e
# OrbitalInclination          orbital_inclination    inc
# Periapsis                   periapsis              omega
# AscendingNode               ascending_node         Omega
# MeanAnomaly                 mean_anomaly           M
#
# IMPORTANT:
# - Elite/Caspian orbital angles are stored in DEGREES.
#   REBOUND expects orbital angles in RADIANS.
#
# - Confirm/convert Caspian units to the REBOUND simulation unit system
#   before adding particles.
#
# Classical orbital elements:
#   a      = semi-major axis
#   e      = eccentricity
#   inc    = inclination
#   Omega  = longitude of ascending node
#   omega  = argument of periapsis
#   M      = mean anomaly
