# Caspian Surveyor - Configuration

This document is intended to be used to understand the directory structure and contents of a Caspian Surveyor installation

## Installation Location (.exe)

### Application Program Directory

- Parent: `%localappdata%\Programs`
- Installation: `%localappdata%\Programs\CaspianSurveyor`
- Installation directory includes all necessary binaries, executables, and licenses

### Application Data Directory

- Parent: `%localappdata%`
- Application Data: `%localappdata%\CaspianSurveyor`

---

#### `%localappdata%\CaspianSurveyor\config\`

`config` contains `overlay_config.json`. This file is used by the color picker within the HUD. Values are hex. If you prefer, you can manually set the hex values within the file itself. Make a backup before manually modifying the file. Be sure to keep formatting and syntax unchanged.

---

#### `%localappdata%\CaspianSurveyor\data\`

`data` contains the `db` directory, `exploration_history.jsonl`, and `historical_event_ingestion.ini`.

---

- `%localappdata%\CaspianSurveyor\data\exploration_history.jsonl` - contains all systems that Caspian Surveyor has ingested. Each line is a json object. This file is written to after jumping to a different system. Duplicated system entries will occur if you repeatedly visit the same system.
- `%localappdata%\CaspianSurveyor\data\historical_event_ingestion.ini` - this file's sole purpose is to let Caspian Surveyor know, at launch, if the history ingestion process needs to occur. Setting this to `True` will re-process systems, but not necessarily add data to SQLite.

---

#### `%localappdata%\CaspianSurveyor\data\db\`

`db` contains the Caspian Surveyor SQLite database and, potentially, backups from previous upgrades.

---

#### `%localappdata%\CaspianSurveyor\data\db\caspian_surveyor.db`

The SQLite database Caspian Surveyor utilizes to archive exploration data. The database contains the following tables:
- systems - basic system information such as system address and position
- bodies - information for discovered bodies; child table of systems
- barycentres - barycentre information; child table of systems
- body_parents - parent_body_id and parent_type; child table of bodies
- body_materials - material name and percentages; child table of bodies
- body_physical_orbital_properties - physical body and orbital motion information; child table of bodies
- body_signals - signals received from bodies (geological, biological, mining locations); child table of bodies
- body_detected_genuses - genus information received after DSS scanning a body; child table of bodies
- body_exobio_scans - exobiology scans; child table of bodies

---

#### `%localappdata%\CaspianSurveyor\logs\`

`logs` contains both CaspianSurveyor and CaspianOverlay log files.

---

#### `%localappdata%\CaspianSurveyor\runtime\`

`runtime` contains the `current_system.json` file. This file is created, generated, and updated constantly as you make discoveries within a system, be it from flying close to a body or utilizing FSS.

---

#### `%localappdata%\CaspianSurveyor\simulation_archives\`

`simulation_archives` stores REBOUND simulation binaries that contain snapshots. The files are named with a UUID and (hopefully) are all unique.

Please be aware that these binaries can become rather large. This largely depends on total snapshots taken of the REBOUND simulation (configured within the REBOUND HUD panel)