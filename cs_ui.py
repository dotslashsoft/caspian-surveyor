import sys

from PySide6 import QtCore, QtWidgets


print(main.EVENT_CONFIG)

sample_body_name = "Blaea Thio EC-Z b41-1 C"

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.align_left = QtCore.Qt.AlignmentFlag.AlignLeft
        self.label = QtWidgets.QLabel("System Name", alignment=self.align_left)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.label)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()

    widget.setWindowTitle("Caspian Surveyor")
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())