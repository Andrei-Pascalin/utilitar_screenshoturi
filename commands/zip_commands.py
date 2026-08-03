from core.command import ICommand
from viewmodels.capture_viewmodel import CaptureViewModel


class CreateZipCommand(ICommand):
    def __init__(self, capture_vm:CaptureViewModel):
        super().__init__()
        self.capture_vm = capture_vm

    def execute(self):
        self.capture_vm.zip_images()