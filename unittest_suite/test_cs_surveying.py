import unittest
from cs_surveying import SurveyState, SurveyDataBuilder


class TestSurveyState(unittest.TestCase):
    def setUp(self):
        # TODO: Initialize instance if needed
        pass

    def test_init(self):
        # TODO: Test SurveyState.__init__
        pass

    def test_begin_system(self):
        # TODO: Test SurveyState.begin_system
        pass

    def test_record_discovery_scan(self):
        # TODO: Test SurveyState.record_discovery_scan
        pass

    def test_record_body_signals(self):
        # TODO: Test SurveyState.record_body_signals
        pass

    def test_record_body_scan(self):
        # TODO: Test SurveyState.record_body_scan
        pass

    def test_mark_all_bodies_found(self):
        # TODO: Test SurveyState.mark_all_bodies_found
        pass

    def test_record_dss_complete(self):
        # TODO: Test SurveyState.record_dss_complete
        pass


class TestSurveyDataBuilder(unittest.TestCase):
    def setUp(self):
        # TODO: Initialize instance if needed
        pass

    def test_init(self):
        # TODO: Test SurveyDataBuilder.__init__
        pass

    def test_build_system_record(self):
        # TODO: Test SurveyDataBuilder.build_system_record
        pass

    def test_build_system_summary(self):
        # TODO: Test SurveyDataBuilder.build_system_summary
        pass

    def test_build_body_record(self):
        # TODO: Test SurveyDataBuilder.build_body_record
        pass


if __name__ == '__main__':
    unittest.main()