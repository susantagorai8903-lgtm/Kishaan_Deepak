"""
app/logger.py
-------------
Creates and configures the application-wide logger.
Import `logger` from this module wherever you need to log.

Usage:
    from app.logger import logger
    logger.info("Model loaded successfully.")
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import config


def _build_logger() -> logging.Logger:
    """Build and return the configured application logger."""
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log = logging.getLogger("kishaan_deepak")
    log.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    # Console handler — always active
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    log.addHandler(console_handler)

    # Rotating file handler — keeps up to 5 × 2 MB log files
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    log.addHandler(file_handler)

    # Prevent duplicate log lines when imported multiple times
    log.propagate = False

    return log


logger: logging.Logger = _build_logger()
