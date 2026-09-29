import logging
import logging.handlers
import os
import sys
import re
from pathlib import Path

# ==========================================================
# Configuration & Sensitive Data Scrubber
# ==========================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(process)d | %(threadName)s | "
    "%(name)s | %(filename)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

SENSITIVE_PATTERNS = [
    (re.compile(r"(password['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", re.IGNORECASE), r"\1***REDACTED***\2"),
    (re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]+", re.IGNORECASE), r"\1***REDACTED_JWT***"),
    (re.compile(r"(api[_-]?key['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", re.IGNORECASE), r"\1***REDACTED_KEY***\2"),
    (re.compile(r"(secret['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", re.IGNORECASE), r"\1***REDACTED_SECRET***\2"),
]


class SanitizedFormatter(logging.Formatter):
    """Formats log messages and automatically redacts credentials/tokens/secrets."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        for pattern, replacement in SENSITIVE_PATTERNS:
            formatted = pattern.sub(replacement, formatted)
        return formatted


# ==========================================================
# Root Logger Setup
# ==========================================================

logger = logging.getLogger("medical_report_analyzer")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

if not logger.handlers:
    formatter = SanitizedFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1. Primary Container Stream Handlers (stdout / stderr)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(LOG_LEVEL)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # 2. Optional File Logging (Development / Host Mounts)
    # Disabled if DISABLE_FILE_LOGGING is true or in constrained container filesystems
    disable_file = os.getenv("DISABLE_FILE_LOGGING", "false").lower() in ("true", "1", "yes")
    if not disable_file:
        try:
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            app_handler = logging.handlers.TimedRotatingFileHandler(
                log_dir / "application.log",
                when="midnight",
                interval=1,
                backupCount=14,
                encoding="utf-8",
            )
            app_handler.setLevel(LOG_LEVEL)
            app_handler.setFormatter(formatter)
            logger.addHandler(app_handler)

            error_handler = logging.handlers.TimedRotatingFileHandler(
                log_dir / "error.log",
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        except Exception:
            # File system might be read-only; container stdout/stderr remains authoritative
            pass


# ==========================================================
# Logger Factory
# ==========================================================

def get_logger(module_name: str) -> logging.Logger:
    """Returns a child logger scoped to module name."""
    return logger.getChild(module_name)