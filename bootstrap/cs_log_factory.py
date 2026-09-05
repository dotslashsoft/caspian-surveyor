import logging
import bootstrap.cs_baseline_config as csconfig
from pathlib import Path
from datetime import datetime
import sys

logger = logging.getLogger(__name__)

class LogManager:
    """
    Configures application logging for Caspian Surveyor.

    Creates the logging directory, generates a timestamped log filename,
    and applies the default logging configuration.
    """
    ### 
    DEFAULT_LOG_DIR = csconfig.run_directory / "logs"
    """Dude, it's in the name. just...read the fucking constant."""

    ###
    DEFAULT_LOG_LEVEL = logging.DEBUG
    """
    default log level.

    TODO: change from static to user facing setting. Even though DEBUG is BEST LOGGING.
    """

    def __init__(self, log_dir=DEFAULT_LOG_DIR) -> None:
        """
        Initializes logging paths and filename information.

        Creates the logging directory if it does not already exist and generates
        a timestamped log filename using the running program's name.

        Args:
            log_dir: Directory in which Caspian Surveyor log files are stored.
                Defaults to DEFAULT_LOG_DIR.
        """     
        self.log_dir = Path(log_dir)
        self.program_name = Path(sys.argv[0]).stem
        self.datetimestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = (f"{self.program_name}_{self.datetimestamp}.log")
        self.full_log_path = (self.log_dir / self.log_filename)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def set_log_config(self) -> None:
        """
        Applies Caspian Surveyor's default file-logging configuration.

        Configures the log file path, log level, file mode, and message format.
        """        
        logging.basicConfig(
            filename=self.full_log_path,
            filemode="a",
            level=self.DEFAULT_LOG_LEVEL,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )