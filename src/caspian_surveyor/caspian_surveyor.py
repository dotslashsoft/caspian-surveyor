import caspian_surveyor.bootstrap.cs_log_factory as cs_log_factory
import caspian_surveyor.cs_history as cs_history
import caspian_surveyor.cs_surveying as Survey
import caspian_surveyor.cs_journal_toolbox as Journal
import caspian_surveyor.runtime.cs_runtime as cs_runtime
import caspian_surveyor.bootstrap.cs_baseline_config as cs_baseline_config
import threading
import logging
import sys
import keyboard
import subprocess
from pathlib import Path
### ### ### ### ### ### ### ### ### ### ### ### 
logger = logging.getLogger(__name__)
#################################
#                               #
### ###   main process    ### ###
#                               #
#################################

def main() -> None:
    """
    The final boss.

    Runs the primary Caspian Surveyor application workflow from startup
    through live journal monitoring:

        - establishes logging configuration
        - locates the latest Elite Dangerous journal
            - exits with status code 2 if no journal is available
        - retrieves the starting events required for state reconstruction
        - creates StateRecovery and reconstructs the current survey state
        - initializes survey-data and history-management components
        - writes the reconstructed current-system record before live 
            monitoring begins
        - creates the fatal-error signaling event
        - starts the journal-directory monitoring thread
        - follows and processes live journal events

    During live processing, FSDJump events finalize the system being left
    and initialize the newly entered system. Other supported journal events
    are delegated to SurveyState and cause the runtime system record to be
    rebuilt when survey state changes.

    Exits with status code 2 if required journal data is unavailable,
    system reconstruction fails, runtime persistence fails, or journal
    monitoring reaches a fatal failure.
    """
    shutdown_event = threading.Event()

    def request_shutdown() -> None:
        logger.info("Global shutdown hotkey received.")
        shutdown_event.set()

    exit_hotkey = keyboard.add_hotkey("ctrl+shift+e", request_shutdown)

    log_manager = cs_log_factory.LogManager()
    log_manager.set_log_config()

    latest_journal = Journal.get_latest_journal_file()

    if latest_journal is None:
        logger.critical("No Elite Dangerous journal file was found. Caspian Surveyor is exiting.")
        sys.exit(2)
    logger.info("Latest journal has been found: %s", latest_journal)   

    latest_journal_events = []
    journal_index = 0

    while not latest_journal_events:
        reconstruction_journal = Journal.get_journal_file_by_index(journal_index)

        if reconstruction_journal is None:
            break

        latest_journal_events = Journal.get_reconstruction_start_events(reconstruction_journal)
        journal_index += 1
    state_recovery = Survey.StateRecovery()
    reconstructed_system = state_recovery.reconstruct_system_data(latest_journal_events)

    if reconstructed_system is None:
        logger.critical("SurveyState system reconstruction failed: returned None. Exiting...")
        sys.exit(2)

    survey_state = state_recovery.survey_state
    survey_data_builder = Survey.SurveyDataBuilder(survey_state)
    data_orchestrator = cs_history.DataOrchestrator()

    system_record = survey_data_builder.build_system_record()

    try:
        runtime_record_written = cs_runtime.write_current_system_record(system_record)
    except OSError:
        logger.exception("Failed to write the current-system runtime record. Exiting...")
        sys.exit(2)

    if not runtime_record_written:
        logger.critical("Current-system runtime record was not written. Exiting...")
        sys.exit(2)

    def launch_overlay() -> subprocess.Popen:
        if getattr(sys, "frozen", False):
            overlay_path = Path(sys.executable).with_name("CaspianOverlay.exe")
            return subprocess.Popen([str(overlay_path)])

        overlay_path = Path(__file__).parent / "ui" / "cs_overlay.py"
        return subprocess.Popen([sys.executable, "-m", "caspian_surveyor.ui.cs_overlay"])
    overlay_process = launch_overlay()

    journal_reader = Journal.JournalReader(latest_journal, poll_interval=1.0)
    fatal_error_event = threading.Event()
    shutdown_event = threading.Event()
    journal_monitor_thread = threading.Thread(
        target=journal_reader.heal_monitor_journal_directory,
        args=(cs_baseline_config.JOURNAL_DIRECTORY, fatal_error_event, shutdown_event)
    )
    try:
        journal_monitor_thread.start()

        for event in journal_reader.follow(fatal_error_event, shutdown_event):
            if fatal_error_event.is_set():
                break

            event_type = event.get("event")
            state_updated = False

            if event_type == "FSDJump":
                # Finalize the system being left.
                logger.debug(f"Result of survey_state.current_system:\t {survey_state.current_system}")
                if survey_state.current_system is not None:
                    system_record = survey_data_builder.build_system_record()
                    runtime_record_written = cs_runtime.write_current_system_record(system_record)

                    if not runtime_record_written:
                        logger.critical("Current-system runtime record was not written. Exiting...")
                        sys.exit(2)

                    data_orchestrator.load_current_system_data_to_dict()
                    data_orchestrator.append_system_record_to_history_file()

                # Begin the system just entered.
                survey_state.begin_system(event)
                system_record = survey_data_builder.build_system_record()
                runtime_record_written = cs_runtime.write_current_system_record(system_record)

                if not runtime_record_written:
                    logger.critical("Current-system runtime record was not written. Exiting...")
                    sys.exit(2)

            else:
                state_updated = survey_state.process_journal_event(event)

            if state_updated:
                system_record = survey_data_builder.build_system_record()
                runtime_record_written = cs_runtime.write_current_system_record(system_record)

                if not runtime_record_written:
                    logger.critical("Current-system runtime record was not written. Exiting...")
                    sys.exit(2)

        if fatal_error_event.is_set():
            logger.critical("Fatal journal monitoring error. Caspian Surveyor is shutting down.")
            sys.exit(2)

    except OSError:
        logger.exception("Failure to read/write a required file. Caspian Surveyor is exiting.")
        sys.exit(2)

    except KeyboardInterrupt:
        print("\nJournal monitoring stopped.")

    finally:
        logger.info("Shutdown event requested")
        shutdown_event.set()
        logger.info("shutdown_event.set() executed.")

        keyboard.remove_hotkey(exit_hotkey)
        logger.info("ctrl+shift+e exit hotkey removed...")

        if journal_monitor_thread.is_alive():
            logger.info("Journal is alive. Joining the threads...")
            journal_monitor_thread.join()

        logger.info("Journal monitor thread joined successfully. Thread alive: %s", journal_monitor_thread.is_alive())

if __name__ == "__main__":
    main()