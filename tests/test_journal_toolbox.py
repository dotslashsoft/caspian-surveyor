import queue
import threading

from pathlib import Path
from unittest.mock import MagicMock

from caspian_surveyor.cs_journal_toolbox import JournalReader

class TestJournalReader:
    def setup_method(self):
        self.journal = JournalReader(
            journal_path=Path("dir"),
            poll_interval=1.0
        )

    def test_journal_path(self):
        assert isinstance(self.journal.journal_path, Path)

    def test_poll_interval(self):
        assert isinstance(self.journal.poll_interval, float)
        assert self.journal.poll_interval == 1.0

    def test_new_journal_queue(self):
        assert isinstance(self.journal.new_journal_queue, queue.Queue)

    def test_consecutive_monitor_failures(self):
        assert isinstance(
            self.journal.consecutive_monitor_failures, int
        )
        assert self.journal.consecutive_monitor_failures == 0


class TestHealMonitorJournalDirectory:
    def setup_method(self):
        self.journal = JournalReader(journal_path=Path("dir"), poll_interval=0.01)
        self.fatal_event = threading.Event()
        self.shutdown_event = threading.Event()

    def test_aborts_after_three_consecutive_failures(self, caplog):
        """Force monitor_journal_directory failing every single time"""
        self.journal.monitor_journal_directory = MagicMock(return_value=False)

        result = self.journal.heal_monitor_journal_directory(
            Path("dir"), self.fatal_event, self.shutdown_event
        )

        assert result is False
        assert self.fatal_event.is_set()
        assert self.journal.consecutive_monitor_failures == 3
        assert self.journal.monitor_journal_directory.call_count == 3
        assert "failed three or more times" in caplog.text

    def test_exits_cleanly_when_shutdown_set_during_monitoring(self):
        """Simulate shutdown happening while monitor_journal_directory runs"""
        def mock_monitor(directory_path, shutdown_event):
            shutdown_event.set()
            return False

        self.journal.monitor_journal_directory = MagicMock(side_effect=mock_monitor)

        result = self.journal.heal_monitor_journal_directory(
            Path("dir"), self.fatal_event, self.shutdown_event
        )

        assert result is None
        assert not self.fatal_event.is_set()
        """Should exit before incrementing failure count because shutdown_event was checked first"""
        assert self.journal.consecutive_monitor_failures == 0

    def test_retries_after_transient_failures(self):
        """Fail twice, then trigger shutdown on the 3rd attempt so the loop terminates cleanly"""
        call_count = 0

        def mock_monitor(directory_path, shutdown_event):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return False
            shutdown_event.set()
            return True

        self.journal.monitor_journal_directory = MagicMock(side_effect=mock_monitor)

        result = self.journal.heal_monitor_journal_directory(
            Path("dir"), self.fatal_event, self.shutdown_event
        )

        assert result is None
        assert not self.fatal_event.is_set()
        assert self.journal.consecutive_monitor_failures == 2
        assert call_count == 3

    def test_exits_during_poll_interval_wait(self):
        """Fail once, then trigger shutdown in a background thread during the wait"""
        self.journal.monitor_journal_directory = MagicMock(return_value=False)
        self.journal.poll_interval = 0.2  # Slightly longer so timer catches it mid-wait

        timer = threading.Timer(0.05, self.shutdown_event.set)
        timer.start()
        try:
            result = self.journal.heal_monitor_journal_directory(
                Path("dir"), self.fatal_event, self.shutdown_event
            )
        finally:
            timer.cancel()

        assert result is None
        assert not self.fatal_event.is_set()
        assert self.journal.monitor_journal_directory.call_count == 1