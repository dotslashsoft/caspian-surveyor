import unittest

import bootstrap.cs_baseline_config as cs_baseline_config
import cs_journal_toolbox as Journal


# class TestJournalToolbox(unittest.TestCase):

#     def test_get_current_system_events(self):
#         fake_journal = (
#             cs_baseline_config.run_directory
#             / "unittest_suite"
#             / "fake_journal.log"
#         )

#         events = Journal.get_current_system_events(
#             fake_journal
#         )

#         self.assertEqual(
#             events[0]["event"],
#             "FSDJump"
#         )

#         self.assertEqual(
#             events[0]["StarSystem"],
#             "SYSTEM B"
#         )

#         self.assertEqual(
#             len(events),
#             4
#         )


if __name__ == "__main__":
    unittest.main()