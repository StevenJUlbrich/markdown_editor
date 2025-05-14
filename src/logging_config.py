import codecs
import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_file: str = "app.log",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
):
    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    log_formatter = logging.Formatter(fmt, datefmt=datefmt)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",  # <-- NEW
    )
    file_handler.setFormatter(log_formatter)

    # wrap sys.stderr/stdout in a UTF-8 writer so CP-1252 never sees the emojis
    utf8_stream = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
    stream_handler = logging.StreamHandler(stream=utf8_stream)
    stream_handler.setFormatter(log_formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(stream_handler)


def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a logger instance for the given module.
    Example: logger = get_logger(__name__)

    This logger instance inherits the configuration set up by `setup_logging`,
    including formatters, handlers, and log levels. Use this function to ensure
    consistent logging across modules.
    """
    return logging.getLogger(module_name)
