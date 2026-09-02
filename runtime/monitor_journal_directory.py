import time
from pathlib import Path
import datetime

journal_directory = (
    Path.home()
    / "Saved Games"
    / "Frontier Developments"
    / "Elite Dangerous"
)


def monitor_journal_directory(directory_path, interval=1):
    """Polls a directory for newly created files."""
    target_dir = Path(directory_path)
    
    if not target_dir.is_dir():
        raise ValueError(f"The path {directory_path} is not a valid directory.")

    print(f"Monitoring folder: {target_dir.resolve()}")
    
    # 1. Establish the baseline of existing files
    # Change to target_dir.rglob('*') to include subdirectories
    existing_files = set(target_dir.glob('*'))
    time_now = datetime.datetime.now()
    print(f"STARTING TIME FOR PROCESS:\t{time_now}")
    try:
        while True:
            time.sleep(interval)
            
            # 2. Check current files
            current_files = set(target_dir.glob('*'))
            
            # 3. Find the difference
            new_files = current_files - existing_files
            
            # process new file
            for file_path in new_files:
                if file_path.is_file():
                    print(file_path)
                    print(f"JOURNAL CREATED:\t{datetime.datetime.now()}")
                    return file_path
                    
            # 5. Update baseline (handles additions and deletions)
            existing_files = current_files
            
    except FileNotFoundError:
        # Crucial for startup if a network drive hasn't mounted yet,
        # or if another startup process deletes/moves the target directory.
        print(f"\nError: The directory '{target_dir}' disappeared or is unavailable.")
        
    except PermissionError:
        # Handles sudden OS lockouts, active antivirus scans on startup,
        # or temporary permission drops on shared network folders.
        print(f"\nError: Lost read permissions for '{target_dir}'.")

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    # Replace with your folder path
    monitor_journal_directory(journal_directory, interval=1)





