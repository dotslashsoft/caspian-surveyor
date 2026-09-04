import json
import logging
import time
import bootstrap.cs_baseline_config as cs_baseline_config
from pathlib import Path
import queue


### ### ### ### ### ### ### ### ### ### ### ###
logger = logging.getLogger(__name__)
journal_directory = cs_baseline_config.journal_directory

class JournalReader:
    """
    One Journal class to rule them all.

    Monitors Elite Dangerous journal files for live activity, detects
    journal rotation, and yields parsed journal events for downstream
    processing.

    Coordinates journal-directory monitoring, queue-based journal swaps,
    and recovery from temporary journal-directory access failures.
    """

    def __init__(self, journal_path: str | Path, poll_interval: float = 1.0) -> None:
        """
        Initializes journal-reading and monitoring state.

        Args:
            journal_path: Path to the Elite Dangerous journal file to begin following.
            poll_interval: Delay, in seconds, between journal and directory checks.
                Defaults to 1.0.
        """     
        self.journal_path = Path(journal_path)
        self.poll_interval = poll_interval
        self.new_journal_queue = queue.Queue()
        self.consecutive_monitor_failures = 0

    def heal_monitor_journal_directory(self, directory_path, fatal_error_event):
        """
        Supervises the Elite Dangerous journal-directory monitor.

        Restarts journal-directory monitoring after recoverable failures. If the
        journal monitor fails three consecutive times, logs a critical error,
        sets fatal_error_event, and returns False.

        Args:
            directory_path: Path to the Elite Dangerous journal directory.
            fatal_error_event: Shared event set when journal monitoring can no
                longer be reliably restored.

        Returns:
            False if journal monitoring fails three consecutive times.
        """  
        logger.debug("heal_monitor_journal_directory called")
        while True:
            monitor_active = self.monitor_journal_directory(directory_path)

            if not monitor_active:
                self.consecutive_monitor_failures += 1
                # Using >= because there WILL be a bug that somehow
                # counts past three and I will lose my mind.
                # Remember this.
                if self.consecutive_monitor_failures >= 3:
                    logger.critical(
                        "Journal monitor has failed three or more "
                        "times consecutively."
                    )

                    logger.critical(
                        "Unable to reliably access the Elite Dangerous "
                        "journal directory. Please:\n"
                        "1. Verify the journal directory exists and is "
                        "accessible.\n"
                        "2. Verify the integrity of your Elite Dangerous "
                        "installation.\n"
                        "3. If the problem persists, locate the latest "
                        "caspian_surveyor*.log file and submit an issue "
                        "via GitHub."
                    )

                    fatal_error_event.set()

                    return False

                logger.warning(
                    "Journal monitor stopped. Attempting to restart "
                    "journal directory monitor."
                )

                time.sleep(self.poll_interval)

    def monitor_journal_directory(self, directory_path):
        """
        Monitors the Elite Dangerous journal directory for newly created journal files.

        When a new journal file is detected, its path is added to new_journal_queue
        for follow() to process and begin reading.

        Runs continuously while the journal directory remains available.

        Args:
            directory_path: Path to the Elite Dangerous journal directory.

        Returns:
            False if monitoring terminates due to a recoverable filesystem error.
        """

        target_dir = Path(directory_path)

        try:
            if not target_dir.is_dir():
                raise FileNotFoundError(f"Journal directory unavailable: {target_dir}")
            
            existing_files = set(target_dir.glob("Journal.*.log"))

            if self.consecutive_monitor_failures != 0:
                logger.info("Journal directory monitor successfully restored.")
                self.consecutive_monitor_failures = 0

            while True:
                time.sleep(self.poll_interval)

                if not target_dir.is_dir():
                    raise FileNotFoundError(f"Journal directory unavailable: {target_dir}")

                current_files = set(target_dir.glob("Journal.*.log"))
                new_files = current_files - existing_files
                
                # process new Journal.*.file found
                for file_path in new_files:
                    if file_path.is_file():
                        self.new_journal_queue.put(file_path)

                existing_files = current_files
                
        except FileNotFoundError:
            logger.exception("The directory '%s' disappeared or is unavailable.", target_dir)
            return False
            
        except PermissionError:
            logger.error("\nError: Lost read permissions for '%s'.", target_dir)
            return False

    def follow(self, fatal_error_event):
        """
        Follows the active Elite Dangerous journal and yields parsed journal events.

        Begins reading the initial journal from the end of the file because
        historical events have already been handled during state reconstruction.

        While following the active journal, checks the new-journal queue for
        journal rotation. When a new journal path is received, closes the current
        journal, opens the new journal, and begins reading it from the beginning.

        Incomplete journal lines are retried after the polling interval, allowing
        Elite Dangerous to finish writing the event before it is parsed.

        Stops following journals when fatal_error_event is set.

        Args:
            fatal_error_event: Shared event used to signal that journal monitoring
                can no longer continue reliably.

        Yields:
            Parsed Elite Dangerous journal events as dictionaries.

        Raises:
            OSError: If the active journal file cannot be opened or read.
        """  
        logger.info("Beginning journal monitoring: %s", self.journal_path)

        current_path = self.journal_path
        new_journal_file = None

        # Outer loop: handles opening and swapping files.
        while not fatal_error_event.is_set():

            try:
                logger.info("Opening journal file: %s",current_path)

                with current_path.open("r", encoding="utf-8") as journal_file:

                    if new_journal_file:
                        journal_file.seek(0, 0)
                        logger.debug("Journal reader starting at beginning of file.")
                        new_journal_file = None

                    else:
                        journal_file.seek(0, 2)
                        logger.debug("Journal reader positioned at end of file.")

                    # Inner loop: reads the current journal.
                    while not fatal_error_event.is_set():

                        try:
                            new_journal_file = (self.new_journal_queue.get_nowait())

                            if new_journal_file:
                                logger.info(
                                    "Swap requested! Switching to: %s",
                                    new_journal_file
                                )

                                current_path = new_journal_file
                                self.new_journal_queue.task_done()

                                break

                        except queue.Empty:
                            pass

                        current_position = journal_file.tell()
                        line = journal_file.readline()

                        if not line:
                            fatal_error_event.wait(self.poll_interval)
                            continue

                        if not line.endswith("\n"):
                            logger.debug("Incomplete journal line encountered; waiting for remaining data.")

                            journal_file.seek(current_position)
                            fatal_error_event.wait(self.poll_interval)
                            continue

                        try:
                            event = json.loads(line)

                        except json.JSONDecodeError:
                            logger.exception("Unable to parse journal line.")
                            continue

                        event_name = event.get("event","Unknown")

                        logger.debug("Journal event received: %s", event_name)

                        if (logger.isEnabledFor(logging.DEBUG) and event_name in DEBUG_LOG_PAYLOAD_EVENTS):
                            logger.debug("Event payload: %s", json.dumps(event))

                        yield event

            except OSError:
                logger.exception(
                    "Unable to open or read journal file: %s", current_path)
                raise

def get_latest_journal_file() -> Path | None:
    """
    It's in the name, brodenheimer.

    Finds the most recently modified Elite Dangerous journal file in the
    configured journal directory.

    Searches for files matching 'Journal.*.log' and selects the newest
    journal based on filesystem modification time.

    Returns:
        Path to the latest Elite Dangerous journal file, or None if the
        journal directory is unavailable or contains no matching files.
    """
    logger.debug("Searching journal directory: %s", journal_directory)

    if not journal_directory.is_dir():
        logger.critical("Elite Dangerous journal directory was not found: %s", journal_directory)
        return None

    journal_files = list(journal_directory.glob("Journal.*.log"))
    logger.debug("Found %d journal files.", len(journal_files))

    if not journal_files:
        logger.warning("No Elite Dangerous journal files found.")
        return None
    latest_journal = max(journal_files, key=lambda path: path.stat().st_mtime)
    logger.info("Latest journal selected: %s", latest_journal)

    return latest_journal

def get_reconstruction_start_events(journal_file: Path) -> list[dict]:
    """
    Retrieves journal events associated with the most recent system context.

    Reads the supplied Elite Dangerous journal from beginning to end and
    retains events beginning with the latest FSDJump or Location event.

    Used by StateRecovery to begin reconstruction of the current system
    survey state.

    Args:
        journal_file: Elite Dangerous journal file to inspect.

    Returns:
        Parsed journal events belonging to the most recent system context
        found in the journal.
    """ 
    latest_system_events = []

    with journal_file.open("r", encoding="utf-8") as file:
        for line in file:
            event = json.loads(line)

            event_type = event.get("event")

            if event_type in {"FSDJump", "Location"}:
                latest_system_events = [event]

            elif latest_system_events:
                latest_system_events.append(event)

    return latest_system_events

def get_journal_file_by_index(index) -> Path | None:
    """
    Gets an Elite Dangerous journal file by recency index.

    Journal files are sorted by modification time from newest to oldest,
    with index 0 representing the most recently modified journal.

    Args:
        index: Position of the journal in the recency-sorted list.

    Returns:
        Path to the journal file at the requested index, or None if the
        index exceeds the number of available journal files.
    """
    logger.debug("Searching journal directory for file index %d: %s", index, journal_directory)

    journal_files = list(journal_directory.glob("Journal.*.log"))
    logger.debug("Found %d journal files.", len(journal_files))

    if index >= len(journal_files):
        return None

    journal_files.sort(key=lambda path: path.stat().st_mtime,reverse=True)
    journal_file = journal_files[index]

    logger.info("Journal file selected at index %d: %s", index, journal_file)

    return journal_file


### event constants ###

DEBUG_LOG_PAYLOAD_EVENTS = {
"""
Elite Dangerous journal events whose full payloads are logged when
DEBUG logging is enabled.
""" 
    "Location",
    "FSDJump",
    "FSSDiscoveryScan",
    "Scan",
    "FSSAllBodiesFound",
    "SAAScanComplete",
    "Shutdown",
    "FSSBodySignals"
}

if __name__ == "__main__":
    pass