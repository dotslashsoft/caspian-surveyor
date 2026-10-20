import rebound
import math
from pprint import pprint
from caspian_surveyor.rebound.caspian_rebound_mappings import CaspianReboundMappings, Rebound

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



sim = rebound.Simulation()
sim.units = ("AU", "yr", "Msun")





class ReboundAdapter:

    def __init__(self) -> None:
        self.mappings = CaspianReboundMappings()


    def convert_caspian_to_rebound(self):
        caspian_mappings = self.mappings.build_rebound_bodies_dict()
        
        for body in caspian_mappings.values():
            if body.body_id == 0:
                sim.add(
                    name=body.body_name,
                    a=body.body_semi_major_axis,
                    e=body.body_eccentricity,
                    inc=math.radians(body.body_orbital_inclination),
                    Omega=math.radians(body.body_ascending_node),
                    omega=math.radians(body.body_periapsis),
                    M=math.radians(body.body_mean_anomaly),
                )
                continue
            
            sim.add(
                name=body.body_name,
                a=body.body_semi_major_axis,
                e=body.body_eccentricity,
                inc=math.radians(body.body_orbital_inclination),
                Omega=math.radians(body.body_ascending_node),
                omega=math.radians(body.body_periapsis),
                M=math.radians(body.body_mean_anomaly),
            )           


if __name__ == '__main__':
    adapter = ReboundAdapter()
    sim = rebound.Simulation()

    sim.units = ("AU", "yr", "Msun")

    adapter.convert_caspian_to_rebound()

    sim.move_to_com()

    # Start browser visualization
    sim.start_server(port=1234)

    # Value is MICROSECONDS.
    sim.usleep = 2500

    print("Simulation running indefinitely.")
    print("Open http://localhost:1234")
    print("CTRL+C to stop.")