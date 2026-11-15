import pytest
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.humanity_relocation_project.humanity_relocation_project import (
    HumanityRelocationProject,
    BodyScoreBreakdown,
    BodyScorer,
    SystemScorer,
    kelvin_to_celsius,
    ms2_to_earth_g,
    bell_curve_score
)
from math import isclose

class TestHumanityRelocationProject:
    def setup_method(self):
        self.hrp = HumanityRelocationProject()
        self.weighted_mappings = self.hrp.weighted_mappings

    def test_class_init(self):
        assert isinstance(self.weighted_mappings, dict)

        total = 0
        for each_value in self.weighted_mappings.values():
            assert isinstance(each_value, float)

            total = total + each_value

        assert total == 1

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

    def test_kelvin_to_celsius(self):
        assert kelvin_to_celsius(0.0) == -273.15
        assert kelvin_to_celsius(273.15) == 0.0
        assert kelvin_to_celsius(373.15) == 100.0