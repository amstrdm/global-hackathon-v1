"""
Centralized logging configuration for the backend application.
Provides structured logging with different levels and proper formatting.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Colors go beep boop"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_file_path: str = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up centralized logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_file_path: Path to log file (defaults to logs/app.log)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """

    # Create logs directory if it doesn't exist
    if log_to_file:
        if log_file_path is None:
            # Create logs directory in the backend folder
            backend_dir = Path(__file__).parent.parent
            logs_dir = backend_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            log_file_path = logs_dir / "app.log"
        else:
            log_file_path = Path(log_file_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("smd_backend")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
    )

    colored_formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    # Prevent duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, creates a child logger.

    Args:
        name: Optional name for the logger (e.g., 'routes.upload', 'utils.db_utils')

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"smd_backend.{name}")
    return logging.getLogger("smd_backend")


# Initialize logging on module import
logger = setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"), log_to_file=True)

# Log startup information
logger.info("Logging system initialized")
logger.info(f"Log level: {logger.level}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
