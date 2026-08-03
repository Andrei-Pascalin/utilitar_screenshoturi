from core.logger import get_logger
from services.notification_service import NotificationService
from ui.main_window import MainWindow
from services.settings_service import SettingsService
from services.capture_service import CaptureService
from services.screenshot_path_service import ScreenshotPathService
from services.image_repository import ImageRepository
from services.zip_service import ZipService
from services.hotkey_service import HotkeyService
from viewmodels.capture_viewmodel import CaptureViewModel

logger = get_logger(__name__)


class MyApp:
    def __init__(self):
        # Main Window

        # Services
        self.settings_service = SettingsService()
        self.settings_service.load_settings()

        self._notification_service = NotificationService()

        self.screenshot_path_service = ScreenshotPathService(settings=self.settings_service.settings)
        self.capture_service = CaptureService(
            settings_service=self.settings_service,
            notification_service=self._notification_service
        )
        self.image_repository = ImageRepository(self.settings_service, self._notification_service)
        self.zip_service = ZipService(self.settings_service,  self._notification_service)
        self.hotkey_service = HotkeyService()

        # ViewModel
        self.capture_viewmodel = CaptureViewModel(
            settings_service=self.settings_service,
            capture_service=self.capture_service,
            image_repository=self.image_repository,
            zip_service=self.zip_service,
            path_service=self.screenshot_path_service,
            hotkey_service=self.hotkey_service,
            notification_service=self._notification_service
        )

        self.main_window = MainWindow(self.capture_viewmodel, self._notification_service)

    def run(self):
        logger.info("Application is running...")
        self.main_window.run()