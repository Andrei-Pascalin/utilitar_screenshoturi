from __future__ import annotations
from typing import TYPE_CHECKING

from core.enums import ObserverEvents
from core.logger import get_logger
from core.observer import IObserver
if TYPE_CHECKING:
    from ui.main_window import MainWindow


class ScreenshotObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self.__logger = get_logger(__name__)
        self._main_window = main_window

    def update(self, event: str, data=None):
        self.__logger.debug(f"Received event:{event} with data:{data}")
        if event is ObserverEvents.DO_IMAGE_ADDED:
            self._main_window.log_widget.add_entry(data)
            self._main_window.browser_widget.refresh_image_browser()

        elif event is ObserverEvents.DO_IMAGE_DELETED:
            self._main_window.log_widget.remove_entry(data)
            self._main_window.browser_widget.refresh_image_browser()

        elif event is ObserverEvents.REFRESH_FIRST_IMAGE_INDEX:
            self._main_window.log_widget.refresh_first_image_index(data)
            self._main_window.browser_widget.refresh_image_browser()

        elif event is ObserverEvents.RELOAD_PICS_FOLDER:
            self._main_window.log_widget.refresh_picture_logs()
            self._main_window.browser_widget.refresh_image_browser()