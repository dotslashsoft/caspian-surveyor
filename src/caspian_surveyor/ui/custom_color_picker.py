from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QColorDialog, QPushButton, QLabel
import caspian_surveyor.bootstrap.cs_baseline_config as cs_baseline_config
import json
import shutil
import sys


class DualColorDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caspian Surveyor: select primary & secondary colors")
        
        # see, I thought I needed a stacked widget, but I realized
        # I didn't need layers, just side-by-side
        pickers_layout = QHBoxLayout()
        
        # left colorful boi
        left_container = QVBoxLayout()
        left_container.addWidget(QLabel("Primary Color"))
        self.primary_picker = QColorDialog()
        self.primary_picker.setOption(QColorDialog.ColorDialogOption.NoButtons, True)
        left_container.addWidget(self.primary_picker)
        pickers_layout.addLayout(left_container)
        
        # right colorful boi
        right_container = QVBoxLayout()
        right_container.addWidget(QLabel("Secondary Color"))
        self.secondary_picker = QColorDialog()
        self.secondary_picker.setOption(QColorDialog.ColorDialogOption.NoButtons, True)
        right_container.addWidget(self.secondary_picker)
        pickers_layout.addLayout(right_container)
        
        # the irony of telling the aforementioned QDialog not to use buttons
        buttons_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        
        self.btn_ok.clicked.connect(self.accept)      # Closes dialog with True status
        self.btn_cancel.clicked.connect(self.reject)  # Closes dialog with False status
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_ok)
        buttons_layout.addWidget(self.btn_cancel)
        
        # AUTOBOTS, ASSEMBLE
        main_layout = QVBoxLayout()
        main_layout.addLayout(pickers_layout)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    # fido, fetch
    def get_colors(self):
        """return both hex codes."""
        return {
            "key_label_color": self.primary_picker.currentColor().name(),
            "value_label_color": self.secondary_picker.currentColor().name()
        }

class ConfigFileHandler:

    def __init__(self) -> None:

        self.APPLICATION_DATA_DIRECTORY = cs_baseline_config.APPLICATION_DATA_DIRECTORY
        self.CONFIG_DIRECTORY = self.APPLICATION_DATA_DIRECTORY / "config" 
        self.OVERLAY_CONFIG = self.CONFIG_DIRECTORY / "overlay_config.json"
        self.TEMP_CONFIG = self.CONFIG_DIRECTORY / "temp_overlay_config.json"
        self.BACKUP_CONFIG = self.CONFIG_DIRECTORY / "backup_overlay_config.json"

    def create_backup_config(self, config_file, backup_config_file):
        # copy config_file to backup_config_file
        if shutil.copy(config_file, backup_config_file):
            print(f"Successfully created {backup_config_file} from {config_file}.")
            return True
        else:
            print(f"Failed to create backup file from {config_file}.")
            return False

    def update_config_file(self, config_file, data_dict):
        with config_file.open("w", encoding="utf-8") as file:
            current_config_data = json.dumps(data_dict, indent=4)
            file.write(current_config_data)

class Workflow:

    def __init__(self) -> None:
        self.file_handler = ConfigFileHandler()
        self.dialog = DualColorDialog()
        self.backup_config = self.file_handler.BACKUP_CONFIG
        self.overlay_config = self.file_handler.OVERLAY_CONFIG
        super().__init__()

    def run_config_workflow(self) -> bool:
        if self.dialog.exec() == QDialog.DialogCode.Accepted:
            self.colors = self.dialog.get_colors()

            self.file_handler.create_backup_config(
                config_file=self.overlay_config, 
                backup_config_file=self.backup_config
            )
            print(self.colors)
            print(f"Success! Key Label Color: {self.colors['key_label_color']}, Value Label Color: {self.colors['value_label_color']}")
            # where I'll add backups, write
            self.file_handler.update_config_file(config_file=self.overlay_config, data_dict=self.colors)
            return True
            
        else:
            print("User cancelled out of picking primary and secondary colors. Exiting...")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    workflow = Workflow()