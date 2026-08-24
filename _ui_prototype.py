import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QTableView
from PySide6 import QtCore
from PySide6.QtGui import QFont, QKeySequence, QShortcut
import traverse_exploration_history
import keyboard



# pre-launch read
system_record = traverse_exploration_history.load_latest_system_record()
ui_data = traverse_exploration_history.build_system_ui_data(system_record)

for planet in ui_data["planet_data"]:
    print(planet["planet_name"])
    print(planet["planet_class"])


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
        self.resize(400, 400)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        
        # I have no idea how the fuck this works
        # UPDATE - I now know how the fuck this 
        #          works. PROGRESS BABY!
        data = [
            ["SYSTEM", (ui_data["system_name"])],
            ["BODIES", str(ui_data["body_count"])],
            ["STARS", str(ui_data["stars"])],
            ["PLANETS", str(ui_data["planets"])],
            ["LANDABLE", str(ui_data["landable"])],
        ]
        # create table
        self.table = QTableWidget()
        self.table_view = QTableView()
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