from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def check_for_updates():
    releases_url = (
        "https://github.com/dotslashsoft/"
        "caspian-surveyor/releases"
    )
    QDesktopServices.openUrl(QUrl(releases_url))