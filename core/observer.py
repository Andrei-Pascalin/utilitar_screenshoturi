from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from core.enums import ObserverEvents
from core.logger import get_logger
from services.notification_service import NotificationType
from ui.main_window import MainWindow

logger = get_logger(__name__)

class IObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: Any = None) -> None:
        """Handle notification from an observable."""
        raise NotImplementedError


class Observable:
    def __init__(self) -> None:
        self._observers: List[IObserver] = []

    def add_observer(self, observer: IObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: IObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: str, data: Any = None) -> None:
        for observer in self._observers:
            observer.update(event, data)

class ScreenshotObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
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

class UIReactObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
        if event is ObserverEvents.DO_PREPARE_UI_CAPTURE:
            self._main_window.save_left_button.config(state="disabled")
            self._main_window.save_right_button.config(state="disabled")
            # Hide GUI so it is not included in the screenshot.
            self._main_window.root.iconify()
        elif event is ObserverEvents.DO_RESTORE_UI:
            self._main_window.root.deiconify()
            self._main_window.save_left_button.config(state="normal")
            self._main_window.save_right_button.config(state="normal")

class StepObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
        if event is ObserverEvents.DO_STEP_UPDATED:
            self._main_window.step_var.set(data)
            logger.debug(f"MainWindow received STEP_UPDATED event. New step: {data}")
        elif event is ObserverEvents.DO_INCREMENT_STEP:
            try:
                current = int(self._main_window.step_var.get())
                logger.debug(f"DO INCREMENT STEP: {current + 1}")
                self._main_window.step_var.set(str(current + 1))
            except ValueError:
                self._main_window.step_var.set("1")

class NotificationObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
        logger.info(f"MainWindow received notification: {event}, data: {data}")

        if data.type == NotificationType.INFO:
            self._main_window.showinfo(data)
        elif data.type == NotificationType.WARNING:
            self._main_window.showwarning(data)
        elif data.type == NotificationType.ERROR:
            self._main_window.showerror(data)
