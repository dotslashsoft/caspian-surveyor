import logging
import bootstrap.cs_baseline_config as csconfig
from pathlib import Path
from datetime import datetime
import sys

logger = logging.getLogger(__name__)

class LogManager:

    DEFAULT_LOG_DIR = csconfig.run_directory / "logs"
    DEFAULT_LOG_LEVEL = logging.DEBUG

    def __init__(self, log_dir=DEFAULT_LOG_DIR):
        self.log_dir = Path(log_dir)
        self.program_name = Path(sys.argv[0]).stem
        self.datetimestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = (f"{self.program_name}_{self.datetimestamp}.log")
        self.full_log_path = (self.log_dir / self.log_filename)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def set_log_config(self):
        logging.basicConfig(
            filename=self.full_log_path,
            filemode="a",
            level=self.DEFAULT_LOG_LEVEL,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def get_log_dir(self):
        return str(self.log_dir)