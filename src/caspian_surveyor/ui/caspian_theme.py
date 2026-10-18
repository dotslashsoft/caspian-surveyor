from pathlib import Path
import caspian_surveyor
from PySide6.QtGui import QFontDatabase


def load_application_font() -> str:
    package_directory = Path(caspian_surveyor.__file__).resolve().parent
    font_path = (package_directory / "assets" / "fonts" / "Electrolize-Regular.ttf")

    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id == -1:
        raise RuntimeError(f"Failed to load application font: {font_path}")

    font_families = QFontDatabase.applicationFontFamilies(font_id)
    if not font_families:
        raise RuntimeError(f"No font family found in: {font_path}")

    return font_families[0]