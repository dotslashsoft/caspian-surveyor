# Caspian Surveyor - First-Launch

Upon launching Caspian Surveyor for the first time, the application reads the journal files within `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\` and reads the file header. If that file header contains the string `Odyssey`, it processes the events within the journal file and archives the data within SQLite.

This process is called *Historical Event Ingestion*. This process takes ~10 seconds per two-thousand systems processed; commanders with a large volume of exploration data within their journals since the release of Odyssey will experience a longer first-time initialization, taking anywhere from four to five minutes, depending on how current the computer's hardware is.

During *Historical Event Ingestion*, a progress bar will display, giving you a visual of the progress being made.

Once that has completed, Caspian Surveyor will be displayed at the top center of your screen.

---
---