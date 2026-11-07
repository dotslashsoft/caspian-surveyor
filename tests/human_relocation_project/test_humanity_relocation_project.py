import pytest
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.humanity_relocation_project.humanity_relocation_project import *

def test_load_current_system():
    hrp = HumanityRelocationProject()

    current_system = hrp._verify_current_system()
    assert current_system is not None
    assert isinstance(current_system, FullStarSystemPayload)

def test_get_fullstarsystempayload():
    hrp = HumanityRelocationProject()

    system_record = hrp._get_fullstarsystempayload(279114075227)
    assert system_record is not None
    assert isinstance(system_record, FullStarSystemPayload)

def test_verify_current_system_invalid(monkeypatch):
    hrp = HumanityRelocationProject()

    monkeypatch.setattr(
        "caspian_surveyor.humanity_relocation_project."
        "humanity_relocation_project.load_current_system_record",
        lambda: None,
    )

    with pytest.raises(
        TypeError,
        match="current_system must be a FullStarSystemPayload",
    ):
        hrp._verify_current_system()

def test_score_complete_system_discovery():
    hrp = HumanityRelocationProject()
    current_system = hrp._verify_current_system()
    complete_discovery = hrp._score_complete_system_discovery(current_system)

    assert complete_discovery is not None
    assert isinstance(complete_discovery, float)

    if current_system.summary.system_fss_complete:
        assert complete_discovery == 100
    else:
        assert complete_discovery >= 0

def test_systemscore_invalid_system_address():
    with pytest.raises(TypeError):
        SystemScore(system_address="abcd")

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            habitability_score="0.0"
        )

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            resource_score="asdf"
        )

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            research_score="asdf"
        )

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            security_score="asdf"
        )

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            economic_score="asdf"
        )

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            raw_score="asdf"
        )

    with pytest.raises(TypeError):
        SystemScore(
            system_address=1234567,
            final_score="asdf"
        )

def test_systemscore_dataclass():
    good_system_score = SystemScore(
        system_address=123456714,
        habitability_score=0.0,
        resource_score=0.0,
        research_score=0.0,
        security_score= 0.0,
        economic_score=0.0,
        raw_score=0.0,
        final_score=0.0
    )

    assert isinstance(good_system_score, SystemScore)

    assert type(good_system_score.system_address) is int
    assert type(good_system_score.habitability_score) is float
    assert type(good_system_score.resource_score) is float
    assert type(good_system_score.research_score) is float
    assert type(good_system_score.security_score) is float
    assert type(good_system_score.economic_score) is float
    assert type(good_system_score.raw_score) is float
