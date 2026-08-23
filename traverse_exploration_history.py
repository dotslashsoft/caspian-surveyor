import main
import json


def load_latest_system_record():

    system_data_information = main.EXPLORATION_HISTORY_FILE

    with open(system_data_information, "r") as open_json:
        last_line = list(open_json)[-1]

    return json.loads(last_line)

def traverse_exploration_jsonl(system_dict):
    for section_name, section_data in system_dict.items():
        if section_name == "system":
            for field_name, field_value in section_data.items():
                print(field_name, field_value)

        if section_name == "summary":
            for field_name, field_value in section_data.items():
                print(field_name, field_value)

        if section_name == "bodies":
            for body_id, body_data in section_data.items():
                for field_name, field_value in body_data.items():
                    if field_name == "materials" and field_value is not None:
                        for material in field_value:
                            print(material["Name"], material["Percent"])
                    else:
                        print(field_name, field_value)

if __name__ == "__main__":
    system_dict = load_latest_system_record()
    traverse_exploration_jsonl(system_dict)