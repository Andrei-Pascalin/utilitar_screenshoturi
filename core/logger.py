import logging
import sys
from typing import Optional, TextIO


def _ensure_logging_configured(stream: Optional[TextIO] = None) -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s:%(name)s:%(message)s",
            stream=stream or sys.stdout,
        )


class AppLogger:
    """Small wrapper around Python's logging module for the app."""

    def __init__(self, name: str, level: int = logging.INFO, stream: Optional[TextIO] = None):
        _ensure_logging_configured(stream)

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = True

        if not self._logger.handlers:
            handler = logging.StreamHandler(stream or sys.stdout)
            handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
            self._logger.addHandler(handler)

    def debug(self, message: str, *args, **kwargs):
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        self._logger.exception(message, *args, **kwargs)


def get_logger(name: str, stream: Optional[TextIO] = None) -> AppLogger:
    return AppLogger(name=name, stream=stream)
