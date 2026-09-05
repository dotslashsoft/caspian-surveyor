import bootstrap.cs_log_factory as cs_log_factory
import cs_history
import cs_surveying as Survey
import cs_journal_toolbox as Journal
import runtime.cs_runtime as cs_runtime
import bootstrap.cs_baseline_config as cs_baseline_config
import threading
import logging
import sys
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
            - returns if no journal is available
        - retrieves the starting events required for state reconstruction
        - creates StateRecovery and reconstructs the current survey state
        - initializes survey-data and history-management components
        - writes the reconstructed current-system record when available
        - creates the fatal-error signaling event
        - starts the journal-directory monitoring thread
        - follows and processes live journal events

    During live processing, FSDJump events finalize the system being left
    and initialize the newly entered system. Other supported journal events
    are delegated to SurveyState and cause the runtime system record to be
    rebuilt when survey state changes.

    Exits with status code 2 if journal monitoring reaches a fatal failure.
    """

    log_manager = cs_log_factory.LogManager()
    log_manager.set_log_config()

    latest_journal = Journal.get_latest_journal_file()

    if latest_journal is None:
        return

    latest_journal_events = Journal.get_reconstruction_start_events(latest_journal)

    state_recovery = Survey.StateRecovery()
    reconstructed_system = state_recovery.reconstruct_system_data(latest_journal_events)

    survey_state = state_recovery.survey_state
    survey_data_builder = Survey.SurveyDataBuilder(survey_state)
    data_orchestrator = cs_history.DataOrchestrator()

    if reconstructed_system is not None:
        system_record = survey_data_builder.build_system_record()
        cs_runtime.write_current_system_record(system_record)

    journal_reader = Journal.JournalReader(latest_journal, poll_interval=1.0)
    fatal_error_event = threading.Event()
    try:
        journal_monitor_thread = threading.Thread(
            target=journal_reader.heal_monitor_journal_directory,
            args=(cs_baseline_config.journal_directory, fatal_error_event)
        )
        
        journal_monitor_thread.start()

        

        for event in journal_reader.follow(fatal_error_event):
            if fatal_error_event.is_set():
                break

            event_type = event.get("event")
            state_updated = False

            if event_type == "FSDJump":
                # Finalize the system being left.
                logger.debug(f"Result of survey_state.current_system:\t {survey_state.current_system}")
                if survey_state.current_system is not None:
                    system_record = survey_data_builder.build_system_record()

                    cs_runtime.write_current_system_record(system_record)
                    data_orchestrator.load_current_system_data_to_dict()
                    data_orchestrator.append_system_record_to_history_file()

                # Begin the system just entered.
                survey_state.begin_system(event)
                system_record = survey_data_builder.build_system_record()
                cs_runtime.write_current_system_record(system_record)

            else:
                state_updated = survey_state.process_journal_event(event)

            if state_updated:
                system_record = survey_data_builder.build_system_record()
                cs_runtime.write_current_system_record(system_record)

        if fatal_error_event.is_set():
            logger.critical("Fatal journal monitoring error. Caspian Surveyor is shutting down.")
            sys.exit(2)

    except KeyboardInterrupt:
        print("\nJournal monitoring stopped.")

if __name__ == "__main__":
    main()