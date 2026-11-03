from caspian_surveyor.runtime.cs_runtime import load_current_system_record


class OverlayAdapter:
    def __init__(self) -> None:
        self.full_system_data = load_current_system_record()

    def call_load_new_system_record(self):
        self.full_system_data = load_current_system_record()

        return self.full_system_data