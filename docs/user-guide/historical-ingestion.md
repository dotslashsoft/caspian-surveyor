# Caspian Surveyor - Historical Ingestion

## Overview

When launching Caspian Surveyor for the first time, the application reads Elite Dangerous: Odyssey journal files, looking to see if the file header contains the string `Odyssey`. If the journal file *does* contain `Odyssey`, then it processes the events within the journal file and archives the data within SQLite.

## Manual Ingestion

### When it is needed
Manual historical event ingestion may be necessary if `caspian_surveyor.db` is corrupted, if you need to upgrade to the next version of Caspian Surveyor and there have been schema changes, or if you're like me and like watching the progress bar.

***NOTE*** Please back up the following files *PRIOR* to performing a manual historical event ingestion:
- exploration_history.jsonl
- caspian_surveyor.db

To backup the files, make a copy of each file and paste them in a directory of your preference. The historical event ingestion process will recreate these files.


## Manually Initiating Historical Event Ingestion
- Ensure Caspian Surveyor is completely closed.
- Navigate to `%LOCALAPPDATA%\CaspianSurveyor\data\`.
- Rename `exploration_history.jsonl` to `exploration_history.backup`.
- Navigate to `%LOCALAPPDATA%\CaspianSurveyor\data\db`.
- Rename `caspian_surveyor.db` to `caspian_surveyor.backup`.
- Navigate back to `%LOCALAPPDATA%\CaspianSurveyor\data\`
- Open `historical_event_ingestion.ini` with your preferred text editor.
- Update `False` to `True`, then save the file.
- Launch Caspian Surveyor