from pathlib import Path

run_directory = Path.cwd()
"""
Working directory from which Caspian Surveyor was launched.

__type__: Path
"""

journal_directory = (
    Path.home()
    / "Saved Games"
    / "Frontier Developments"
    / "Elite Dangerous"
)
"""
Path to the Elite Dangerous journal directory.

__type__: Path
"""