import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QTableView
from PySide6 import QtCore
from PySide6.QtGui import QFont
import keyboard
import data_structures

ui_data = data_structures.load_latest_system_record()

class SystemTable(QMainWindow):

    toggle_requested  = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self.toggle_requested.connect(self.toggle_widget)

        keyboard.add_hotkey(
            "ctrl+shift+m",
            self.toggle_requested.emit
        )

        self.setWindowTitle("Caspian Surveyor")
        self.resize(455, 515)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        
        # I have no idea how the fuck this works
        # UPDATE - I now know how the fuck this 
        #          works. PROGRESS BABY!
        data = [
            ["SYSTEM", str(ui_data.system.name)],
            ["ADDRESS", str(ui_data.system.address)],
            ["POSITION", str(ui_data.system.position)],
            ["BODY COUNT", str(ui_data.system.body_count)],
            ["SCANNED", str(ui_data.summary.scan_records)],
            ["STARS", str(ui_data.summary.stars)],
            ["PLANETS", str(ui_data.summary.planets)],
            ["ASTEROID BELTS", str(ui_data.summary.belt_clusters)],
            ["UNKNOWN", str(ui_data.summary.unknown_scan_objects)],
            ["LANDABLE", str(ui_data.summary.landable)],
            ["HMC WORLDS", str(ui_data.summary.hmc)],
            ["TERRAFORM HMC", str(ui_data.summary.tf_hmc)],
            ["WATER WORLDS", str(ui_data.summary.water_worlds)],
            ["TERRAFORM WW", str(ui_data.summary.tf_water_worlds)],
            ["EARTHLIKE WORLDS", str(ui_data.summary.earthlike_worlds)],
            ["AMMONIA WORLDS", str(ui_data.summary.ammonia_worlds)],
        ]
        # create table
        self.table = QTableWidget()
        self.table.setFont(QFont("Eurostile", 12))
        self.table.setStyleSheet("QTableWidget { background: transparent; }")
        self.table.viewport().setStyleSheet("background: transparent;")
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        
        self.table.setRowCount(len(data))
        self.table.setColumnCount(2)

        # data population
        for row_idx, (attribute, value) in enumerate(data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(attribute))
            self.table.setItem(row_idx, 1, QTableWidgetItem(value))

        self.setCentralWidget(self.table)
        self.table.resizeColumnsToContents()

    def toggle_widget(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemTable()
    window.show()
    sys.exit(app.exec())