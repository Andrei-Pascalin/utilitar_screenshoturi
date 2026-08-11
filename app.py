# pylint: disable=missing-docstring,line-too-long

from core.logger import get_logger
from ui.main_window import MainWindow
from services.notification_service import NotificationService
from services.settings_service import SettingsService
from services.capture_service import CaptureService
from services.screenshot_path_service import ScreenshotPathService
from services.image_repository import ImageRepository
from services.zip_service import ZipService
from services.hotkey_service import HotkeyService
from viewmodels.capture_viewmodel import CaptureViewModel
from viewmodels.settings_viewmodel import SettingsViewModel


class MyApp:
    def __init__(self, logger):
        self.__logger = logger

        # folosim __ pentru private si pentru name manglening
        # Services
        self.__settings_service = SettingsService()
        self.__settings_service.set_logger(logger)
        self.__settings_service.load_settings()
        proper_logger = get_logger(__name__)
        self.__settings_service.set_logger(proper_logger)

        self.__logger = proper_logger

        self.__notification_service = NotificationService()

        self.__screenshot_path_service = ScreenshotPathService()
        self.__capture_service = CaptureService(
            notification_service=self.__notification_service
        )
        self.__image_repository = ImageRepository(self.__notification_service)
        self.__zip_service = ZipService(self.__notification_service)
        self.__hotkey_service = HotkeyService()

        self.__settings_viewmodel = SettingsViewModel()

        # ViewModel
        self.__capture_viewmodel = CaptureViewModel(
            settings_viewmodel=self.__settings_viewmodel,
            capture_service=self.__capture_service,
            image_repository=self.__image_repository,
            zip_service=self.__zip_service,
            path_service=self.__screenshot_path_service,
            hotkey_service=self.__hotkey_service,
            notification_service=self.__notification_service
        )

        # Main Window
        self.main_window = MainWindow(self.__capture_viewmodel,
                                      self.__settings_viewmodel,
                                      self.__notification_service)

    def run(self):
        self.__logger.info("Application is running...")
        self.main_window.run()
