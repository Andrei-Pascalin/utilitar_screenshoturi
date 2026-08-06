from abc import ABC, abstractmethod


class ICommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute command with optional arguments."""
        raise NotImplementedError