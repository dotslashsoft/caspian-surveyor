import rebound
import logging
from pprint import pprint
from caspian_surveyor.rebound.caspian_to_rebound_data_prep import CaspianDataHandler

logger = logging.getLogger(__name__)


class ReboundAdapter:
    def __init__(self) -> None:
        self.handler = CaspianDataHandler()
        self.sim = rebound.Simulation()