import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

_root_logger: Optional[logging.Logger] = None


def configure_logger(level: int = logging.DEBUG, log_path: Optional[str] = None) -> logging.Logger:
    """Configure and return the shared root logger."""
    global _root_logger
    if _root_logger is None:
        _root_logger = logging.getLogger("WinMigrate")
    if log_path is None:
        log_path = os.path.join(os.getcwd(), "winmigrate.log")

    for handler in list(_root_logger.handlers):
        _root_logger.removeHandler(handler)

    _root_logger.setLevel(level)
    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    _root_logger.addHandler(stream_handler)
    _root_logger.addHandler(file_handler)
    return _root_logger


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a child logger of the shared root logger."""
    if _root_logger is None:
        configure_logger()
    return logging.getLogger("WinMigrate").getChild(name)
