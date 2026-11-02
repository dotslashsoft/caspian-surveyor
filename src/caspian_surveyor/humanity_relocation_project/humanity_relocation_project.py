from pprint import pprint
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.runtime.cs_runtime import *
from typing import Any

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
    def __init__(self) -> None:
        self.current_system = load_current_system_record()

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




    def evaluate_final_system_score(self):
        pass


class SystemScore:
    """Class containing all scoring criteria"""
    def __init__(self) -> None:
        pass

    def _initialize_scoring_dictionary(self) -> dict[str, Any]:
        scoring_dict = {}
        return scoring_dict

    def _calculate_system_habitability(self):
        pass

    def _calculate_system_economic_potential(self):
        pass

    def _calculate_system_security(self):
        pass


if __name__ == '__main__':
    hrp = HumanityRelocationProject()
    system_record = hrp._get_fullstarsystempayload(279114075227)
    pprint(system_record, sort_dicts=False)
