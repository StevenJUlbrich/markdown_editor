import logging
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_file: str = "app.log", max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5
):
    """
    Sets up project-wide logging configuration.
    Uses rotating file handler to prevent infinite growth.
    Adds per-module logger support and optional metadata tags.
    Call this early in your main entry points.

    Parameters:
    - log_file (str): The name of the log file to write to.
    - max_bytes (int): Maximum size of each log file in bytes.
    - backup_count (int): Number of backup files to retain.
    """
    log_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(log_formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # Clear existing handlers to avoid duplicates
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a logger instance for the given module.
    Example: logger = get_logger(__name__)

    This logger instance inherits the configuration set up by `setup_logging`,
    including formatters, handlers, and log levels. Use this function to ensure
    consistent logging across modules.
    """
    return logging.getLogger(module_name)
