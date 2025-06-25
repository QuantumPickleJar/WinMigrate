import logging


def get_logger(name: str = "WinMigrate") -> logging.Logger:
    """Return a configured logger shared across the application."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Log to console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Log to file
        file_handler = logging.FileHandler('winmigrate.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
