import pytest
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.humanity_relocation_project.humanity_relocation_project import *

def test_load_current_system():
    hrp = HumanityRelocationProject()
    assert hrp.current_system is not None
    assert isinstance(hrp.current_system, FullStarSystemPayload)

def test_get_fullstarsystempayload():
    hrp = HumanityRelocationProject()

    system_record = hrp._get_fullstarsystempayload(279114075227)
    assert system_record is not None
    assert isinstance(system_record, FullStarSystemPayload)

def test_verify_current_system():
    hrp = HumanityRelocationProject()
    assert isinstance(hrp._verify_current_system(), FullStarSystemPayload)

    with pytest.raises(TypeError):
        hrp._verify_current_system(None)

def test_score_complete_system_discovery():
    hrp = HumanityRelocationProject()
    current_system = hrp._verify_current_system()
    complete_discovery = hrp._score_complete_system_discovery(current_system)

    assert complete_discovery is not None
    assert isinstance(complete_discovery, int)

    assert complete_discovery == 100