# pylint: disable=missing-docstring,line-too-long

from __future__ import annotations
from typing import TYPE_CHECKING

from core.enums import ObserverEvents
from core.logger import get_logger
from core.observer import IObserver

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class StepObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self.__logger = get_logger(__name__)
        self._main_window = main_window

    def update(self, event: str, data=None):
        self.__logger.debug(f"Received event:{event} with data:{data}")
        if event is ObserverEvents.DO_STEP_UPDATED:
            self._main_window.step_var.set(data)
            self.__logger.debug(f"MainWindow received STEP_UPDATED event. New step: {data}")
        # elif event is ObserverEvents.DO_INCREMENT_STEP:
        #     try:
        #         current = int(self._main_window.step_var.get())
        #         self.__logger.debug(f"DO INCREMENT STEP: {current + 1}")
        #         self._main_window.step_var.set(str(current + 1))
        #     except ValueError:
        #         self._main_window.step_var.set("1")