import main
import json

system_data_information = main.EXPLORATION_HISTORY_FILE

with open(system_data_information, "r") as open_json:
    last_line = (list(open_json)[-1])

system_dict = json.loads(last_line)

for key, value in system_dict.items():
    if key == "schema_version":
        print(key, value)

    if key == "system":
        for key, value in value.items():
            print(key, value)

    if key == "summary":
        for key, x in value.items():
            print(key,x)

    if key == "bodies":
        for key1, value1 in value.items():
            for key2, value2 in value1.items():

                if key2 == "materials" and value2 is not None:
                    for each_material in value2:
                        print(f"materials:\t{each_material}")
                else:
                    print(key2, value2)
