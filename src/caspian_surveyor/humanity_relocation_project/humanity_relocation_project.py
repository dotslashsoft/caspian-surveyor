from math import isfinite, sqrt, trunc
from pprint import pprint
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.runtime.cs_runtime import *
from typing import Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

"""_summary_
The priority system is for role-playing strictly and
its intention is to give exploration a little more narrative
while also providing (relatively) accurate scientific data
in which certain criteria will utilize.

As you venture out into the void, you're tasked with
a simple mission: to find the best 'Sol' replacement
system possible.

Scoring will be from 0 - X, where X is 'the best possible
replacement'. That is in quotes, because out of one-hundred
billion systems, there will be better systems discovered,
statistically speaking.

Things to note and/or look for:

    === HABITABLE WORLDS ===
    - Earthlike Worlds
        - This will be the highest scoring entity, almost
            immediately placing it in "HIGH" priority

    - Candidates for terraforming:
        - Water Worlds
        - High Metal Content (HMC) planets
        - Rocky bodies
        - Metal-rich bodies

    - Distance between valuable planets (intra-system)
    - Long-term system stability (REBOUND BOIII)

    === RESOURCE EXTRACTION POTENTIAL ===
    - Ringed planets
        - Gas giants
        - Dwarf and minor planets
        - Terrestrial and rocky bodies
        - Stellar remnants
            - Brown dwarfs
    - Asteroid belts
        - Resource types
    - Planetary bodies (surface and gas)
        - Pristine high-value surface minerals
        - Gas giants (yes, ED universe mentions resource extraction
            from gas giants)

    === SCIENCE AND RESEARCH ===
    - Notable stellar phenomena
    - Biological signals
    - High celestial body diversity
    - 3+ stars (PHYSICS BOIIIIIIIIII)

    === AREA ("Exo-Bubble") ===
    - Are the neighboring systems high-value?
        - Resources
        - Terrestrial planets
            - TFWW
            - TFHMC
            - TFRB
            - TFMR

    === SECURITY (brainstorming currently) ===
    - Ideas
        - Distance from bubble
            - Are you settling for a power or will you pioneer and
                begin a new civilization
        - Distance from thargoids
        - Have you found raxxla? Dark Wheel?
            - Automatic MVP, 9000 DKP....PLUS!
            - No really...
            - pls tell me

    === ECONOMY (brainstorming currently) ===
    - Ideas
        - Resource values
        - Neighboring stars habitability
        - Neutron star highway proximity
        - Terrestrial planets

"""


class HumanityRelocationProject:
    """Temporary class for Humanity Relocation Project"""
    def _get_fullstarsystempayload(self, system_address) -> FullStarSystemPayload:
        system_query = ArchivedSystemQueries()
        connection = ConnectionManager()
        conn = connection.establish_db_connection()

        try:
            connection.initialize_schema(conn)
            payload = system_query.get_archived_system_info(conn, system_address)

            verified_payload = self._verify_fullstarsystempayload(payload)
            return verified_payload

        finally:
            connection.close_db_connection(conn)

    def _verify_fullstarsystempayload(self, payload) -> FullStarSystemPayload:
        if not isinstance(payload, FullStarSystemPayload):
            raise TypeError("current_system must be a FullStarSystemPayload")

        return payload

    def _verify_current_system(self) -> FullStarSystemPayload:
        current_system = load_current_system_record()
        if not isinstance(current_system, FullStarSystemPayload):
            raise TypeError("current_system must be a FullStarSystemPayload")

        return current_system

    def _score_complete_system_discovery(self, current_system: FullStarSystemPayload) -> float:
        if current_system.summary.system_fss_complete:
            return 100.0

        return 50.0

    # distance from sol: sqrt((x2 - x1)**2 + (y2 - y1)**2)
    def _get_distance_from_sol(self, system: FullStarSystemPayload) -> float:
        position_x = system.system.system_position[0]
        position_y = system.system.system_position[1]
        position_z = system.system.system_position[2]

        distance_from_sol = sqrt(position_x**2 + position_y**2 + position_z**2)
        return round(distance_from_sol)



@dataclass(frozen=True)
class CriterionResult:
    key: str
    raw_score: float
    weighted_points: float

    def __post_init__(self):
        if type(self.key) is not str:
            raise TypeError("key must be a string.")

        if type(self.raw_score) is not float:
            raise TypeError("raw_score must be a float.")

        if type(self.weighted_points) is not float:
            raise TypeError("weighted_points must be a float.")

        if not isfinite(self.raw_score) or not 0.0 <= self.raw_score <= 100.0:
            raise ValueError(
                f"raw_score for '{self.key}' must be between 0.0 and 100.0. "
                f"Value received: {self.raw_score}"
            )

        if not isfinite(self.weighted_points) or not 0.0 <= self.weighted_points <= 100.0:
            raise ValueError(
                f"weighted_points for '{self.key}' must be between 0.0 and 100.0."
            )


@dataclass(frozen=True)
class SystemScore:
    system_address: int

    rubric_version: str
    criteria: tuple[CriterionResult, ...]
    preliminary: bool = False

    def __post_init__(self):
        if type(self.system_address) is not int:
            raise TypeError("system_address must be an integer")

        if type(self.rubric_version) is not str:
            raise TypeError("rubric_version must be a string")

        if type(self.criteria) is not tuple:
            raise TypeError("criteria must be a tuple with CriterionResults")

        if type(self.preliminary) is not bool:
            raise TypeError("preliminary must be a bool")

    @property
    def final_score(self) -> float:
        return sum(
            (criterion.weighted_points for criterion in self.criteria),
            0.0
        )

if __name__ == '__main__':
    hrp = HumanityRelocationProject()
    payload = hrp._get_fullstarsystempayload(18253501780267)
    pprint(payload, sort_dicts=False)

    distance = hrp._get_distance_from_sol(payload)
    print(f"Distance from Sol: ~{distance} ly")