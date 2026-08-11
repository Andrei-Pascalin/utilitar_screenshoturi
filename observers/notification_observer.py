
from __future__ import annotations
from typing import TYPE_CHECKING

from core.logger import get_logger
from core.observer import IObserver

if TYPE_CHECKING:
    from ui.main_window import MainWindow

# clasa care asculta daca trebuie sa se afiseze un messagebox pe ecran, daca da ... main_wiindow...
class NotificationObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self.__logger = get_logger(__name__)
        self._main_window = main_window

    def update(self, event: str, data=None):
        self.__logger.info(f"MainWindow received notification: {event}, data: {data}")
        self._main_window.show_notification(data)
