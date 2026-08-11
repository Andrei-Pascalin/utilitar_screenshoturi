from __future__ import annotations
from typing import TYPE_CHECKING

from core.enums import ObserverEvents
from core.logger import get_logger
from core.observer import IObserver

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class UIReactObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self.__logger = get_logger(__name__)
        self._main_window = main_window

    def update(self, event: str, data=None):
        self.__logger.debug(f"Received event:{event} with data:{data}")
        if event is ObserverEvents.DO_PREPARE_UI_CAPTURE:
            self._main_window.save_left_button.config(state="disabled")
            self._main_window.save_right_button.config(state="disabled")
            # Hide GUI so it is not included in the screenshot.
            self._main_window.root.iconify()
        elif event is ObserverEvents.DO_RESTORE_UI:
            self._main_window.root.deiconify()
            self._main_window.save_left_button.config(state="normal")
            self._main_window.save_right_button.config(state="normal")
