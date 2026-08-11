# pylint: disable=missing-docstring,line-too-long

from abc import ABC, abstractmethod


class ICommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute command."""
        raise NotImplementedError