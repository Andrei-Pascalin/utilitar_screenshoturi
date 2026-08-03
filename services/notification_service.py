# pylint: disable=missing-docstring,line-too-long

from dataclasses import dataclass
from enum import StrEnum, auto

from core.enums import ObserverEvents
from core.observer import Observable


class NotificationType(StrEnum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()

@dataclass
class Notification:

    type: NotificationType

    title: str

    message: str

class NotificationService:

    def __init__(self):
        self.notification = Observable()

    def error(self, title, message):
        self.notification.notify(
            ObserverEvents.NOTIFICATION,
            Notification(
                NotificationType.ERROR,
                title,
                message
            )
        )

    def warning(self, title, message):
        self.notification.notify(
            ObserverEvents.NOTIFICATION,
            Notification(
                NotificationType.WARNING,
                title,
                message
            )
        )

    def info(self, title, message):
        self.notification.notify(
            ObserverEvents.NOTIFICATION,
            Notification(
                NotificationType.INFO,
                title,
                message
            )
        )