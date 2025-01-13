import logging
from pathlib import Path
from datetime import datetime

class Logger:
    """Simple logger."""
    
    def __init__(self):
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("tree_forcast")
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create file handler
        current_time = datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(f"logs/pre-proccess_{current_time}.log")
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    def getLogger(self):
        return self.logger
    def debug(self, message: str) -> None:
         """Log debug message."""
         self.logger.debug(message)
    def info(self, message: str) -> None:
         """Log debug message."""
         self.logger.info(message)
    def eror(self, message: str) -> None:
         """Log debug message."""
         self.logger.error(message)

# Create a singleton instance
logger = Logger()#.getLogger()
