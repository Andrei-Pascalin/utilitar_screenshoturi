from core.command import ICommand
from viewmodels.capture_viewmodel import CaptureViewModel

class IncrementStepCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        self.capture_vm = capture_vm

    def execute(self, *args, **kwargs):
        self.capture_vm.increment_step()

class DecrementStepCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        self.capture_vm = capture_vm

    def execute(self, *args, **kwargs):
        self.capture_vm.decrement_step()

class CaptureWindowCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        self.capture_vm = capture_vm

    def execute(self, source, *args, **kwargs):
        self.capture_vm.capture_img(source)

class ReloadPicsCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        self.capture_vm = capture_vm

    def execute(self, *args, **kwargs):
        self.capture_vm.reload_pics()

