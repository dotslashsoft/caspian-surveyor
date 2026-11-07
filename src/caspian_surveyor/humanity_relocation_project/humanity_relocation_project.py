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
    def _get_fullstarsystempayload(self, system_address) -> FullStarSystemPayload | None:
        """Query SQLite for a system and reconstruct its FullStarSystemPayload.

        Args:
            system_address (int): Address of the system to reconstruct.

        Returns:
            FullStarSystemPayload | None: Reconstructed system data if successful,
            otherwise None.
        """
        system_query = ArchivedSystemQueries()
        connection = ConnectionManager()
        conn = connection.establish_db_connection()

        try:
            connection.initialize_schema(conn)
            payload = system_query.get_archived_system_info(conn, system_address)

            return payload
        finally:
            connection.close_db_connection(conn)

    def _verify_current_system(self) -> FullStarSystemPayload:
        current_system = load_current_system_record()
        if not isinstance(current_system, FullStarSystemPayload):
            raise TypeError("current_system must be a FullStarSystemPayload")

        return current_system

    def _score_complete_system_discovery(self, current_system: FullStarSystemPayload) -> float:
        if current_system.summary.system_fss_complete:
            return 100.0

        return 50.0

    def _evaluate_final_system_score(self):
        pass


@dataclass
class SystemScore:
    system_address: int

    habitability_score: float = 0.0
    resource_score: float = 0.0
    research_score: float = 0.0
    security_score: float = 0.0
    economic_score: float = 0.0

    raw_score: float = 0.0
    final_score: float = 0.0

    def __post_init__(self):
        if type(self.system_address) is not int:
            raise TypeError("system_address must be an integer")

        if type(self.habitability_score) is not float:
            raise TypeError("habitability_score must be a float")

        if type(self.resource_score) is not float:
            raise TypeError("resource_score must be a float")

        if type(self.research_score) is not float:
            raise TypeError("research_score must be a float")

        if type(self.security_score) is not float:
            raise TypeError("security_score must be a float")

        if type(self.economic_score) is not float:
            raise TypeError("economic_score must be a float")

        if type(self.raw_score) is not float:
            raise TypeError("raw_score must be a float")

        if type(self.final_score) is not float:
            raise TypeError("final_score must be a float")


if __name__ == '__main__':
    hrp = HumanityRelocationProject()
    system_record = hrp._get_fullstarsystempayload(279114075227)
    pprint(system_record, sort_dicts=False)
