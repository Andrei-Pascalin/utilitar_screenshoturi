# pylint: disable=missing-docstring,line-too-long

import logging
import sys
from typing import Optional, TextIO

from core.enums import ApplicationSettingsEnum
from services.settings_service import SettingsService


class AppLogger:
    """Small wrapper around Python's logging module for the app."""

    def __init__(self, name: str, stream: Optional[TextIO] = None):
        settings_service = SettingsService()
        level = settings_service.get_setting(ApplicationSettingsEnum.LOG_LEVEL)

        formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)-8s | %(name)s | "
                                          "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
                                          datefmt="%Y-%m-%d %H:%M:%S")

        logging.getLogger().setLevel(level)
        logging.getLogger("PIL").setLevel(logging.ERROR)

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False

        if not self._logger.handlers:
            handler = logging.StreamHandler(stream or sys.stdout)
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def debug(self, message: str, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        self._logger.exception(message, *args, **kwargs)


def get_logger(name: str, stream: Optional[TextIO] = None) -> AppLogger:
    return AppLogger(name=name, stream=stream)
