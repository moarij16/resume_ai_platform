"""
Logging configuration for the ATS Resume Scanner.

Provides a centralized logger with configurable levels and consistent formatting.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    verbose: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure the root logger for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        verbose: If True, sets level to DEBUG.
        log_file: Optional path to write logs to a file.
    """
    log_level = logging.DEBUG if verbose else level
    root = logging.getLogger("scanner")
    root.setLevel(log_level)

    if root.handlers:
        return

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(fmt)
    root.addHandler(handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger for a module.

    Args:
        name: Module name (e.g., __name__).

    Returns:
        Logger instance.
    """
    if name.startswith("scanner"):
        return logging.getLogger(name)
    return logging.getLogger(f"scanner.{name}")
