import json
import unittest

from cs_history import DataOrchestrator
import bootstrap.cs_baseline_config as cs_baseline_config


class TestDataOrchestrator(unittest.TestCase):

    def setUp(self):
        self.test_directory = (cs_baseline_config.run_directory / "unittest_suite")

        self.TEST_EXPLORATION_HISTORY_FILE = (self.test_directory / "test_exploration_history.jsonl")
        self.TEST_CURRENT_SYSTEM_FILE = (self.test_directory / "test_current_system.json")
        self.FAKE_DATA_FILE = (self.test_directory / "fake_data.json")

        self.test_directory.mkdir(parents=True,exist_ok=True)

        with self.FAKE_DATA_FILE.open("r", encoding="utf-8") as fake_file:
            self.current_system_data = json.load(fake_file)

        self.TEST_CURRENT_SYSTEM_FILE.write_text(json.dumps(self.current_system_data), encoding="utf-8")

        self.data_orchestrator = DataOrchestrator(self.TEST_CURRENT_SYSTEM_FILE,self.TEST_EXPLORATION_HISTORY_FILE)

    def test_load_current_system_data_to_dict(self):
        load_result = (self.data_orchestrator.load_current_system_data_to_dict())

        self.assertEqual(load_result,self.current_system_data)

    def test_append_system_record_to_history_file(self):
        load_result = (self.data_orchestrator.load_current_system_data_to_dict())
        append_result = (self.data_orchestrator.append_system_record_to_history_file())
        self.assertTrue(append_result)

        with self.TEST_EXPLORATION_HISTORY_FILE.open("r", encoding="utf-8") as file:
            lines = file.readlines()

        written_data = json.loads(lines[-1])
        self.assertEqual(written_data, load_result)

    def test_append_without_loaded_data_returns_false(self):
        result = (
            self.data_orchestrator
            .append_system_record_to_history_file()
        )

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()