"""Centralized logging for Flash Automator."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Callable, Optional

DEFAULT_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_log_listeners: list[Callable[[str, int, str], None]] = []


class CallbackLogHandler(logging.Handler):
    """Logging handler that invokes registered listeners (e.g. Qt UI widgets)."""

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        for listener in _log_listeners:
            try:
                listener(msg, record.levelno, record.levelname)
            except Exception:
                pass


def add_log_listener(callback: Callable[[str, int, str], None]) -> None:
    """Register a listener for log records: callback(formatted_msg, level_no, level_name)."""
    if callback not in _log_listeners:
        _log_listeners.append(callback)


def remove_log_listener(callback: Callable[[str, int, str], None]) -> None:
    """Remove a registered log listener."""
    if callback in _log_listeners:
        _log_listeners.remove(callback)


def setup_logger(
    name: str = "flash_automator",
    log_dir: Optional[str | Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Set up and return the application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Callback Handler for UI
    callback_handler = CallbackLogHandler()
    callback_handler.setFormatter(formatter)
    callback_handler.setLevel(level)
    logger.addHandler(callback_handler)

    # File Handler
    if log_dir is None:
        log_dir = Path.home() / ".flash_automator" / "logs"
    else:
        log_dir = Path(log_dir)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / "flash_automator.log"
        file_handler = logging.FileHandler(str(file_path), encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file log handler: {e}")

    return logger


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """Obtain a child logger or the root flash_automator logger."""
    if module_name:
        return logging.getLogger(f"flash_automator.{module_name}")
    return logging.getLogger("flash_automator")
