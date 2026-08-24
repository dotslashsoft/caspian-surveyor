import main
import json


def load_latest_system_record():

    system_data_information = main.EXPLORATION_HISTORY_FILE

    with open(system_data_information, "r") as open_json:
        last_line = list(open_json)[-1]

    system_record = json.loads(last_line)
    return system_record


def inspect_system_record(system_dict):
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

def build_system_ui_data(system_record):
    system = system_record["system"]
    summary = system_record["summary"]
    bodies = system_record["bodies"]

    planets = []

    for body_id, body_data in sorted(bodies.items(), key=lambda item: int(item[0])):
        if body_data.get("planet_class") is not None:
            planets.append({
                "body_id": body_data["body_id"],
                "planet_name": body_data["body_name"],
                "planet_class": body_data["planet_class"],
                "planet_tfs": body_data["terraform_state"],
                "surface_pressure": body_data["surface_pressure"],
                "periapsis": body_data["periapsis"],
                "was_discovered": body_data["was_discovered"],
                "was_mapped": body_data["was_mapped"],
                "was_footfalled": body_data["was_footfalled"],
            })

    return {
        "system_name": system["name"],
        "system_address": system["address"],
        "position": system["position"],
        "body_count": system["body_count"],
        "stars": summary["stars"],
        "planets": summary["planets"],
        "landable": summary["landable"],
        "planet_data": planets,
    }


### main execution ###

if __name__ == "__main__":
    system_dict = load_latest_system_record()
    print(build_system_ui_data(system_dict))