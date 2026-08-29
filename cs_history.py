import json
import bootstrap.cs_baseline_config as cs_basline_config


EXPLORATION_HISTORY_FILE = (cs_basline_config.run_directory / "exploration_history.jsonl")

def append_system_record_to_history_file(summary):
    with EXPLORATION_HISTORY_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(summary) + "\n")