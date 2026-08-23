import main
import json

system_data_information = main.EXPLORATION_HISTORY_FILE

with open(system_data_information, "r") as open_json:
    last_line = (list(open_json)[-1])

system_dict = json.loads(last_line)

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
