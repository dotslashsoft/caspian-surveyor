import pytest
from tests.conftests import sample_journal_file
from caspian_surveyor.cs_survey_data import SurveyDataAggregator
from pathlib import Path
import json


class TestSurveyDataAggregator:
    def setup_method(self):
        self.survey_data = SurveyDataAggregator()

    def test_get_current_system_before_initialization(self):
        event = {"SystemAddress": 10477373803}
        result = self.survey_data._get_current_system(event)
        assert result is None

    def test_get_current_system_matching_address(self, sample_journal_file: Path):
        with sample_journal_file.open("r", encoding="utf-8") as file:
            fsdjump_event = json.loads(file.readline())

        self.survey_data.begin_system(fsdjump_event)
        result = self.survey_data._get_current_system(fsdjump_event)

        assert result is not None
        assert result is self.survey_data.current_system
        assert result["system_name"] == "Sol"
        assert result["system_address"] == 10477373803

    def test_get_current_system_mismatched_address(self, sample_journal_file: Path):
        with sample_journal_file.open("r", encoding="utf-8") as file:
            fsdjump_event = json.loads(file.readline())

        self.survey_data.begin_system(fsdjump_event)
        event = {"SystemAddress": 999999999}

        result = self.survey_data._get_current_system(event)
        assert result is None

    def test_get_current_system_without_address(self, sample_journal_file: Path):
        with sample_journal_file.open("r", encoding="utf-8") as file:
            fsdjump_event = json.loads(file.readline())

        self.survey_data.begin_system(fsdjump_event)
        event = {"event": "Scan"}

        result = self.survey_data._get_current_system(event)
        assert result is self.survey_data.current_system