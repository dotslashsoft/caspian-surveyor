import caspian_surveyor.bootstrap.cs_log_factory as cs_log_factory
import caspian_surveyor.cs_history as cs_history
import caspian_surveyor.cs_survey_data as Survey
import caspian_surveyor.cs_journal_toolbox as Journal
import caspian_surveyor.runtime.cs_runtime as cs_runtime
from caspian_surveyor.bootstrap.cs_baseline_config import JOURNAL_DIRECTORY
from caspian_surveyor.db.database_adapter import SqliteDataAdapter
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.ui.historical_ingestion_progress import HistoryProgressbar, HistoryIngestionSignals
from caspian_surveyor.ui.caspian_theme import load_application_font
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
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
    shutdown_event = threading.Event()

    def request_shutdown() -> None:
        logger.info("Global shutdown hotkey received.")
        shutdown_event.set()

    exit_hotkey = keyboard.add_hotkey("ctrl+shift+e", request_shutdown)

    log_manager = cs_log_factory.LogManager()
    log_manager.set_log_config()

    history = Journal.HistoricalJournalIngestion()
    if history.check_historical_event_ingestion_flag():
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        font_family = load_application_font()
        app.setFont(QFont(font_family))

        progress_window = HistoryProgressbar()
        progress_signals = HistoryIngestionSignals()
        progress_signals.progress.connect(progress_window.update_progress_bar)
        progress_window.show()

        QTimer.singleShot(0, progress_window.raise_)
        QTimer.singleShot(0, progress_window.activateWindow)

        ingestion_errors = []

        def run_historical_ingestion() -> None:
            try:
                history.process_and_persist_historical_journal_events(
                    progress_callback=progress_signals.progress.emit
                )
            except Exception as exc:
                ingestion_errors.append(exc)
                progress_signals.failed.emit(str(exc))
            else:
                progress_signals.finished.emit()

        progress_signals.finished.connect(progress_window.close)
        progress_signals.finished.connect(app.quit)

        progress_signals.failed.connect(lambda _error_message: progress_window.close())
        progress_signals.failed.connect(lambda _error_message: app.quit())

        history_ingestion_thread = threading.Thread(
            target=run_historical_ingestion,
            name="HistoricalIngestion",
        )
        history_ingestion_thread.start()
        app.exec()
        history_ingestion_thread.join()

        if ingestion_errors:
            logger.critical(
                "Historical journal ingestion failed: %s",
                ingestion_errors[0],
            )
            sys.exit(2)

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

    connection_manager = ConnectionManager()
    sql_adapter = SqliteDataAdapter()
    archived_system_queries = ArchivedSystemQueries()

    conn = connection_manager.establish_db_connection()
    connection_manager.initialize_schema(conn)

    state_recovery = Survey.StateRecovery()

    oldest_matching_index = state_recovery.find_oldest_matching_journal_index(
        latest_journal_events
    )

    if oldest_matching_index is None:
        logger.critical("No matching journal reconstruction point found.")
        sys.exit(2)

    recovery_journal = Journal.get_journal_file_by_index(
        oldest_matching_index
    )

    if recovery_journal is None:
        logger.critical("Recovery journal could not be located.")
        sys.exit(2)


    recovery_events = Journal.get_reconstruction_start_events(
        recovery_journal
    )

    if not recovery_events:
        logger.critical("No reconstruction events found in recovery journal.")
        sys.exit(2)

    recovery_start_event = recovery_events[0]
    system_address = recovery_start_event.get("SystemAddress")
    archived_payload = None

    if system_address is not None:
        archived_payload = archived_system_queries.get_archived_system_info(
            conn,
            system_address
        )

    logger.info(
        "Startup archive lookup: SystemAddress=%s, archived=%s",
        system_address,
        archived_payload is not None
    )

    reconstructed_system = state_recovery.recover_current_system_state(
        latest_journal_events,
        archived_payload=archived_payload
    )

    if reconstructed_system is None:
        logger.critical("SurveyDataAggregator system reconstruction failed: returned None. Exiting...")
        sys.exit(2)

    survey_data_aggregator = state_recovery.survey_data_aggregator
    survey_data_builder = Survey.SurveyDataBuilder(survey_data_aggregator)
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

    journal_monitor_thread = threading.Thread(
        target=journal_reader.heal_monitor_journal_directory,
        args=(JOURNAL_DIRECTORY, fatal_error_event, shutdown_event)
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
                logger.debug(
                    "Result of survey_state.current_system:\t %s",
                    survey_data_aggregator.current_system
                )

                if survey_data_aggregator.current_system is not None:
                    system_record = survey_data_builder.build_system_record()
                    runtime_record_written = cs_runtime.write_current_system_record(system_record)

                    if not runtime_record_written:
                        logger.critical("Current-system runtime record was not written. Exiting...")
                        sys.exit(2)

                    # Persist departing system to SQLite.
                    if system_record is not None:
                        sql_adapter.persist_current_system_record(conn, system_record)

                    data_orchestrator.load_current_system_data_to_dict()
                    data_orchestrator.append_system_record_to_history_file()

                # Begin the system just entered.
                survey_data_aggregator.begin_system(event)

                system_address = event.get("SystemAddress")

                reconstructed_system = archived_system_queries.get_archived_system_info(
                    conn,
                    system_address
                )

                if reconstructed_system is not None:
                    logger.info(
                        "Previously archived system found: %s",
                        event.get("StarSystem")
                    )

                    survey_data_aggregator.restore_archived_system(
                        reconstructed_system
                    )

                system_record = survey_data_builder.build_system_record()
                runtime_record_written = cs_runtime.write_current_system_record(system_record)

                if not runtime_record_written:
                    logger.critical("Current-system runtime record was not written. Exiting...")
                    sys.exit(2)

            else:
                state_updated = survey_data_aggregator.process_journal_event(event)

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

        connection_manager.close_db_connection(conn)

        logger.info("Journal monitor thread joined successfully. Thread alive: %s", journal_monitor_thread.is_alive())

if __name__ == "__main__":
    main()