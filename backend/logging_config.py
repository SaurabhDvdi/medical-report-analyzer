import logging
import logging.handlers
import os
from pathlib import Path

# ==========================================================
# Configuration
# ==========================================================

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(process)d | %(threadName)s | "
    "%(name)s | %(filename)s:%(lineno)d | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==========================================================
# Root Logger
# ==========================================================

logger = logging.getLogger("medical_report_analyzer")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

if not logger.handlers:

    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt=DATE_FORMAT
    )

    # ------------------------------------------------------
    # Console
    # ------------------------------------------------------

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # ------------------------------------------------------
    # General Log
    # ------------------------------------------------------

    app_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "application.log",
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
    )

    app_handler.setLevel(LOG_LEVEL)
    app_handler.setFormatter(formatter)

    # ------------------------------------------------------
    # Error Log
    # ------------------------------------------------------

    error_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )

    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(app_handler)
    logger.addHandler(error_handler)

# ==========================================================
# Logger Factory
# ==========================================================


def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a child logger.

    Example:
        logger = get_logger(__name__)
    """
    return logger.getChild(module_name)