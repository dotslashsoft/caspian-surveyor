from caspian_surveyor.runtime.cs_runtime import load_current_system_record

class OverlayAdapter:

    def __init__(self) -> None:
        self.full_system_data = load_current_system_record()

    def call_load_new_system_record(self):
        self.full_system_data = load_current_system_record()
        # print("\ncall_load_new_system_record\n")
        return self.full_system_data

    def get_system_data(self):
        if self.full_system_data is None:
            return
        return self.full_system_data.system

    def get_summary_data(self):
        if self.full_system_data is None:
            return

        return self.full_system_data.summary

    def get_planetary_body_data(self):
        if self.full_system_data is None:
            return

        self.planetary_bodies = self.full_system_data.planetary_bodies

        return self.planetary_bodies