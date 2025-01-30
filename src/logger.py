import logging
from datetime import datetime
import os
class Logger(logging.Logger):
    """
    Singleton logger class that handles file logging.
    Creates a new log file daily in the logs directory.
    """

    def __init__(self,logger_name,logs_dir,log_mode='DEBUG'): 
        
        # Create logger
        log_level = getattr(logging, log_mode.upper())
        super().__init__(logger_name, log_level)

        #Insure thet the folder is existing
        logs_path = os.path.join(logs_dir, "logs")
        os.makedirs(logs_path, exist_ok=True)
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create file handler
        current_time = datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(os.path.join(logs_path, f"{logger_name}-{current_time}.log"),mode='a')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.addHandler(file_handler)

