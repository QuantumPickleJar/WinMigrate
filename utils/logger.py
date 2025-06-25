import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "WinMigrate") -> logging.Logger:
    """Return a configured logger shared across the application."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fmt = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmt)

        # Stream handler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Rotating file handler to keep log history
        log_path = os.path.join(os.getcwd(), 'winmigrate.log')
        file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    return logger
