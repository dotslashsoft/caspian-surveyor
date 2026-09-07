from pathlib import Path
import os

WORKING_DIRECTORY =  Path(os.environ["LOCALAPPDATA"]) / "CaspianSurveyor"
"""
Working directory from which Caspian Surveyor was launched.

__type__: Path
"""

journal_directory = (Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous")
"""
Path to the Elite Dangerous journal directory.

__type__: Path
"""

RUNTIME_DIRECTORY = Path(WORKING_DIRECTORY / "runtime")
