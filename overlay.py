import sys
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, 
    QVBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
import data_structures

import keyboard

class MetricWidget(QWidget):
    """Reusable HUD data block (Label on top, Value below)"""
    
    def __init__(self, key: str, default_value: str = "--"):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(1)

        # color of headings (SYSTEM, BODIES, STARS, etc.)
        self.key_label = QLabel(key)
        self.key_label.setStyleSheet("color: #7d8b99; font-size: 9px; font-weight: bold; letter-spacing: 1px;  font-family: Eurostile;")

        # color of values (Blaea Thio EC-Z b41-1, 12, 3, true, etc.)
        self.val_label = QLabel(default_value)
        self.val_label.setStyleSheet("color: #56cffc; font-size: 13px; font-weight: bold; font-family: Eurostile;")

        layout.addWidget(self.key_label)
        layout.addWidget(self.val_label)

    def set_value(self, value: str | int | float):
        self.val_label.setText(str(value))

class JournalWorker(QtCore.QObject):
    system_updated = QtCore.Signal(object)

    def run(self):
        print("Journal worker is running")


class SystemInfoOverlay(QWidget):
    toggle_requested  = QtCore.Signal()
    exit_requested = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.toggle_requested.connect(self.toggle_widget)
        self.exit_requested.connect(QApplication.instance().quit)
        
        keyboard.add_hotkey(
            "ctrl+shift+m",
            self.toggle_requested.emit
        )

        keyboard.add_hotkey(
            "ctrl+shift+e",
            self.exit_requested.emit
        )

        self.ui_data = data_structures.load_latest_system_record()

        if self.ui_data is not None:
            self.planetary_bodies = self.ui_data.planetary_bodies
        else:
            self.planetary_bodies = []

        self.current_body_index = 0
        self.debug_planetary_bodies()
        ### window flags for overlay ###
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |       # Always stay over the game window
            Qt.WindowType.FramelessWindowHint |        # Remove OS title bar and borders
            Qt.WindowType.Tool                         # Hides from taskbar / Alt+Tab
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Alpha transparency
        self.init_ui()

        # create worker thread
        self.journal_thread = QtCore.QThread()
        self.journal_worker = JournalWorker()

        self.journal_worker.moveToThread(self.journal_thread)
        self.journal_thread.started.connect(self.journal_worker.run)

        self.journal_thread.start()
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.refresh_system_data)
        self.update_timer.start(5000)
        # Temporary sanity check

    def debug_planetary_bodies(self):
        for body in self.planetary_bodies:
            print(body.body_id)
            print(body.body_name)
            print(body.planet_class)


    def refresh_system_data(self):
        ui_data = data_structures.load_latest_system_record()
    
        if ui_data is None:
            return
    
        self.metric_system.set_value(ui_data.system.name.upper())
        self.metric_body_count.set_value(ui_data.system.body_count)
        self.metric_stars.set_value(ui_data.summary.stars)
        self.metric_planets.set_value(ui_data.summary.planets)
        self.metric_tfhmc.set_value(ui_data.summary.hmc)
        self.metric_tfww.set_value(ui_data.summary.tf_water_worlds)
        self.metric_elw.set_value(ui_data.summary.earthlike_worlds)
    
        self.position_top_center()

    def toggle_widget(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            
    def init_ui(self):
        # but have you heard of titan ass theory™?
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        ui_data = data_structures.load_latest_system_record()
        # seriously.
        panel = QFrame()
        panel.setObjectName("HUDPanel")
        # solid border -> translucent -
        panel.setStyleSheet("""
                #HUDPanel {
                    background-color: rgba(0, 0, 0, 100);
                    border-top: 1px solid #002e4d;
                    border-bottom: 1px solid #004d80;
                    border-radius: 4px;
                    border-left: none;
                    border-right: none;
                }
        """)

        # the universe is but an atom. (heh)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        # full background glowy thing color. 
        # it's okay to laugh
        # OG was orange. Please look up EDHM and never use orange again. Game changer
        # shadow.setColor(QColor(255, 113, 0, 100))
        #shadow.setColor(QColor(0, 166, 220, 50))
        shadow.setColor(QColor(0, 0, 0, 0))
        shadow.setOffset(0, 0)
        panel.setGraphicsEffect(shadow)

        # on the ass of
        hud_layout = QHBoxLayout(panel)
        hud_layout.setContentsMargins(12, 6, 12, 6)
        hud_layout.setSpacing(6)

        # a extra-universal titan
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        app_title = QLabel("CASPIAN")
        # color of CASPIAN
        app_title.setStyleSheet("color: #56cffc; font-size: 12px; font-weight: 900; letter-spacing: 2px;")
        app_title.setFont("Eurostile")
        # color of SURVEYOR
        # yes, I'm aware it's obvious. NOW. But in weeks to come
        # when my ADHD ass forgets, you'll be happy a simple bug 
        # fix doesn't take 10 days
        app_sub = QLabel("SURVEYOR")
        app_sub.setStyleSheet("color: #7d8b99; font-size: 8px; font-weight: bold; letter-spacing: 1px;")
        app_sub.setFont("Eurostile")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)
        hud_layout.addLayout(title_box)

        hud_layout.addWidget(self._create_separator())

        # prove me wrong
        
        self.metric_system = MetricWidget("SYSTEM", ui_data.system.name.upper())
        self.metric_body_count = MetricWidget("BODIES", str(ui_data.system.body_count))
        self.metric_stars = MetricWidget("STARS", str(ui_data.summary.stars))
        self.metric_planets = MetricWidget("PLANETS", str(ui_data.summary.planets))
        self.metric_elw = MetricWidget("ELW", str(ui_data.summary.earthlike_worlds))
        self.metric_tfww = MetricWidget("TFWW", str(ui_data.summary.tf_water_worlds))
        self.metric_tfhmc = MetricWidget("TFHMC", str(ui_data.summary.tf_hmc))



        for metric in [self.metric_system, self.metric_body_count, self.metric_stars, 
                       self.metric_planets, self.metric_elw, self.metric_tfww, self.metric_tfhmc  ]:
            hud_layout.addWidget(metric)
            if metric != self.metric_tfhmc:
                hud_layout.addWidget(self._create_separator())

        outer_layout.addWidget(panel)
        self.setLayout(outer_layout)
    

    def _create_separator(self) -> QFrame:
        """Creates a subtle vertical divider line between metrics."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("color: rgba(0, 122, 124, 25);")
        return line

    def position_top_center(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        self.adjustSize()
        x = (screen_geometry.width() - self.width()) // 2
        y = 20
        self.move(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = SystemInfoOverlay()
    overlay.show()
    overlay.position_top_center()
    sys.exit(app.exec())