import json
import logging
import time
import bootstrap.cs_baseline_config as cs_baseline_config
from pathlib import Path
import queue


### ### ### ### ### ### ### ### ### ### ### ###
logger = logging.getLogger(__name__)
run_directory = cs_baseline_config.run_directory
journal_directory = cs_baseline_config.journal_directory

class JournalReader:

    def __init__(self, journal_path, poll_interval=1.0):
        self.journal_path = Path(journal_path)
        self.poll_interval = poll_interval
        self.new_journal_queue = queue.Queue()
        self.consecutive_monitor_failures = 0

    def heal_monitor_journal_directory(self, directory_path, fatal_error_event):

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
        Monitor the Elite Dangerous journal directory.

        Runs continuously while the journal directory remains available.

        Returns:
            False if monitoring terminates due to a recoverable
            filesystem error.
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

def get_latest_journal_file():
    logger.debug("Searching journal directory: %s", journal_directory)

    if not journal_directory.is_dir():
        logger.critical("Elite Dangerous journal directory was not found: %s", journal_directory)
        return None

    journal_files = list(journal_directory.glob("Journal.*.log"))
    logger.debug("Found %d journal files.", len(journal_files))

    if not journal_files:
        logger.warning("No Elite Dangerous journal files found.")
        return None


def get_latest_system_events(journal_file: Path) -> list[dict]:
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

def get_journal_file_by_index(index):
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
    "Location",
    "FSDJump",
    "FSSDiscoveryScan",
    "Scan",
    "FSSAllBodiesFound",
    "SAAScanComplete",
    "Shutdown"
}

if __name__ == "__main__":
    pass