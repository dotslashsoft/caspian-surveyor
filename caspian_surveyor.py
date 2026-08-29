import bootstrap.cs_log_factory as cs_log_factory
import cs_history
import cs_surveying as Survey
import cs_journal_toolbox as Journal
### ### ### ### ### ### ### ### ### ### ### ### 

###############################################################
#                                                             #
### ###                 main process                    ### ###
#                                                             #
###############################################################

def main():
    log_manager = cs_log_factory.LogManager()
    log_manager.set_log_config()

    # display_directory_info()

    latest_journal = Journal.list_journal_directory_contents()
    if latest_journal is None:
        return

    reader = Journal.JournalReader(latest_journal, poll_interval=1.0)
    survey_state = Survey.SurveyState()
    survey_data_builder = Survey.SurveyDataBuilder(survey_state)
    print(f"Monitoring:\t\t{latest_journal}")

    try:
        for event in reader.follow():
            event_type = event.get("event")

            print(f"{event.get('timestamp')} | {event_type}")

            if event_type == "FSDJump":
                survey_state.begin_system(event)

            elif event_type == "FSSDiscoveryScan":
                survey_state.record_discovery_scan(event)

            elif event_type == "Scan":
                survey_state.record_body_scan(event)

            elif event_type == "FSSBodySignals":
                survey_state.record_body_signals(event)

            elif event_type == "SAAScanComplete":
                survey_state.record_dss_complete(event)

            elif event_type == "FSSAllBodiesFound":
                newly_complete = (
                    survey_state.mark_all_bodies_found(event))

                if newly_complete:
                    print("FSS survey complete.")

                    system_record = survey_data_builder.build_system_record()
                    cs_history.append_system_record_to_history_file(system_record)

    except KeyboardInterrupt:
        print("\nJournal monitoring stopped.")

if __name__ == "__main__":
    main()