from pathlib import Path
import os

APPLICATION_DATA_DIRECTORY =  Path(os.environ["LOCALAPPDATA"]) / "CaspianSurveyor"
"""
Root application-data directory for Caspian Surveyor.

__type__: Path
"""

RUNTIME_DIRECTORY = APPLICATION_DATA_DIRECTORY / "runtime"

JOURNAL_DIRECTORY = (Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous")
"""
Path to the Elite Dangerous journal directory.

__type__: Path
"""