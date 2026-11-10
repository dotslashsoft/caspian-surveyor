import pytest
from dataclasses import FrozenInstanceError
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.humanity_relocation_project.humanity_relocation_project import (
    HumanityRelocationProject,
    SystemScore,
    CriterionResult
)

class TestHumanityRelocationProject:
    def setup_method(self):
        self.hrp = HumanityRelocationProject()

    @pytest.mark.integration
    def test_load_current_system(self):
        current_system = self.hrp._verify_current_system()
        assert current_system is not None
        assert isinstance(current_system, FullStarSystemPayload)

    @pytest.mark.integration
    def test_get_fullstarsystempayload(self):
        system_record = self.hrp._get_fullstarsystempayload(279114075227)
        assert system_record is not None
        assert isinstance(system_record, FullStarSystemPayload)




class TestSystemScoreDataclass:
    def setup_method(self):
        self.hrp = HumanityRelocationProject()

    def test_systemscore_is_frozen(self):
        good_system_score = SystemScore(
            system_address=123456714,
            rubric_version="1",
            criteria=(
                CriterionResult("ready_to_host", 0.0, 0.0),
                CriterionResult("terraformable", 0.0, 0.0),
                CriterionResult("body_diversity", 100.0, 25.0),
            ),
            preliminary=True
        )

        with pytest.raises(FrozenInstanceError):
            good_system_score.system_address = 0 # type: ignore[misc]

    def test_verify_current_system_invalid(self, monkeypatch):
        monkeypatch.setattr(
            "caspian_surveyor.humanity_relocation_project."
            "humanity_relocation_project.load_current_system_record",
            lambda: None,
        )

        with pytest.raises(TypeError,match="current_system must be a FullStarSystemPayload"):
            self.hrp._verify_current_system()

    def test_score_complete_system_discovery(self):
        current_system = self.hrp._verify_current_system()
        complete_system_score = self.hrp._score_complete_system_discovery(current_system)

        assert complete_system_score is not None
        assert isinstance(complete_system_score, float)

        if current_system.summary.system_fss_complete:
            assert complete_system_score == 100
        else:
            assert complete_system_score >= 0

    def test_systemscore_invalid_system_address(self):
        with pytest.raises(TypeError):
            SystemScore(
                system_address="abcd", # type: ignore[misc]
                rubric_version="1",
                criteria=(
                    CriterionResult("ready_to_host", 0.0, 0.0),
                    CriterionResult("terraformable", 0.0, 0.0),
                    CriterionResult("body_diversity", 100.0, 25.0),
                ),
            )

    def test_systemscore_invalid_rubric_version(self):
        with pytest.raises(TypeError):
            SystemScore(
                system_address=1234567,
                rubric_version=1, # type: ignore[misc]
                criteria=(
                    CriterionResult("ready_to_host", 0.0, 0.0),
                    CriterionResult("terraformable", 0.0, 0.0),
                    CriterionResult("body_diversity", 100.0, 25.0),
                ),
            )

    def test_systemscore_preliminary(self):
        with pytest.raises(TypeError):
            SystemScore(
                system_address=1234567,
                rubric_version="asdf",
                criteria=(
                    CriterionResult("ready_to_host", 12.0, 0.0),
                    CriterionResult("terraformable", 0.0, 0.0),
                    CriterionResult("body_diversity", 100.0, 25.0),
                ),
                preliminary=10 # type: ignore[misc]
            )

    def test_systemscore_dataclass(self):
        good_system_score = SystemScore(
            system_address=123456714,
            rubric_version="1",
            criteria=(
                CriterionResult("ready_to_host", 0.0, 0.0),
                CriterionResult("terraformable", 0.0, 0.0),
                CriterionResult("body_diversity", 100.0, 25.0),
            ),
            preliminary=True
        )

        assert isinstance(good_system_score, SystemScore)
        assert isinstance(good_system_score.system_address, int)
        assert isinstance(good_system_score.rubric_version, str)
        assert isinstance(good_system_score.criteria, tuple)

    def test_systemscore_final_score(self):
        system_score = SystemScore(
            system_address=123456714,
            rubric_version="1",
            criteria=(
                CriterionResult("ready_to_host", 100.0, 50.0),
                CriterionResult("terraformable", 50.0, 12.5),
                CriterionResult("body_diversity", 75.0, 18.75),
            ),
        )

        assert system_score.final_score == 81.25


class TestCriterionResultDataclass:
    def test_criterionresult_is_frozen(self):
        criterion_result = CriterionResult(
            key="1",
            raw_score=1.0,
            weighted_points=1.0
        )

        with pytest.raises(FrozenInstanceError):
            criterion_result.key = "5" # type: ignore[misc]

    def test_criterionresult_raw_score_high(self):
        """Verifies raw_score cannot accept values > 100.0"""
        with pytest.raises(ValueError):
            CriterionResult(
                key="1",
                raw_score=100.1,
                weighted_points=25.0
            )

    def test_criterionresult_raw_score_low(self):
        """Verifies raw_score cannot accept values < 0.0"""
        with pytest.raises(ValueError):
            CriterionResult(
                key="1",
                raw_score=-0.1,
                weighted_points=25.0
            )

    def test_criterionresult_invalid_key(self):
        """Verifies key only accepts string type values."""
        with pytest.raises(TypeError):
            CriterionResult(
                key=1, # type: ignore[misc]
                raw_score=78.4,
                weighted_points=89.2
            )

    def test_criterionresult_invalid_raw_score(self):
        """Verifies raw_score only accepts float type values."""
        with pytest.raises(TypeError):
            CriterionResult(
                key="1",
                raw_score=78,
                weighted_points=45.8
            )

    def test_criterionresult_invalid_weighted_points(self):
        """Verifies weighted_points only accepts float type values."""
        with pytest.raises(TypeError):
            CriterionResult(
                key="1",
                raw_score=90.3,
                weighted_points=45
            )