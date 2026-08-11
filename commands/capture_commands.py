# pylint: disable=missing-docstring,line-too-long

from core.logger import get_logger
from core.command import ICommand
from viewmodels.capture_viewmodel import CaptureViewModel
from viewmodels.settings_viewmodel import SettingsViewModel


class IncrementStepCommand(ICommand):
    def __init__(self, settings_vm:SettingsViewModel):
        super().__init__()
        self.__logger = get_logger(__name__)
        self.settings_vm = settings_vm

    def execute(self, *args, **kwargs):
        self.__logger.info("Increment execute ...")
        self.settings_vm.increment_step()

class DecrementStepCommand(ICommand):
    def __init__(self, settings_vm:SettingsViewModel):
        super().__init__()
        self.__logger = get_logger(__name__)
        self.settings_vm = settings_vm

    def execute(self, *args, **kwargs):
        self.__logger.debug("Decrement execute ...")
        self.settings_vm.decrement_step()

class CaptureWindowCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        # self.__logger = get_logger(__name__)
        self.capture_vm = capture_vm

    def execute(self, *args, **kwargs):
        # args[0] should be the window source name, ex: CaptureMode.LEFT_MONITOR or "AppName_1"
        self.capture_vm.capture_img(args[0])

class ReloadPicsCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        # self.__logger = get_logger(__name__)
        self.capture_vm = capture_vm

    def execute(self, *args, **kwargs):
        self.capture_vm.reload_pics()

