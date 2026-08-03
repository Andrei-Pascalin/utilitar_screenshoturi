from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


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