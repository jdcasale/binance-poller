import logging

from utils.config import Config

def setup_logging(name: str):
    # Set up basic logging configuration
    logging.basicConfig(
        level=Config().get_log_level(),  # This sets the log level to DEBUG
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
    )
    return logging.getLogger(name)
