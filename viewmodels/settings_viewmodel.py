# pylint: disable=missing-docstring,line-too-long

from core.observer import Observable
from core.enums import ApplicationSettingsEnum as SETTINGS_E
from core.enums import ObserverEvents
from core.logger import get_logger
from services.settings_service import SettingsService
from utils.validation import validate_step


class SettingsViewModel(Observable):
    def __init__(self):
        super().__init__()
        self.settings_service = SettingsService()
        self.__logger = get_logger(__name__)

    def save_settings(self):
        self.settings_service.save_settings()

    def update_settings(self,
                        work_dir=None,
                        rc=None,
                        sci=None,
                        step=None,
                        create_step_folder=None,
                        auto_increment_step=None,
                        step_no_index_delimiter=None,
                        selected_window_name=None,
                        image_browser_geometry=None,
                        main_window_geometry=None):
        self.work_dir = work_dir
        self.rc = rc
        self.sci = sci
        self.step = step
        self.create_step_folder = create_step_folder
        self.auto_increment_step = auto_increment_step
        self.step_no_index_delimiter = step_no_index_delimiter
        self.selected_window_name = selected_window_name
        self.image_browser_geometry = image_browser_geometry
        self.main_window_geometry = main_window_geometry

    def increment_step(self):
        self.__logger.debug(f"Incrementing ++ step from {self.step}")
        self.step += 1

    def decrement_step(self):
        self.__logger.debug(f"Decrementing -- step from {self.step}")
        self.step -= 1

    # ------------------------------------------------------------------
    # Settings state properties
    # ------------------------------------------------------------------

    @property
    def log_level(self):
        return self.settings_service.get_setting(SETTINGS_E.LOG_LEVEL)

    @property
    def work_dir(self):
        return self.settings_service.get_setting(SETTINGS_E.WORK_DIR)

    @work_dir.setter
    def work_dir(self, value):
        self.settings_service.set_setting(SETTINGS_E.WORK_DIR, value)

    @property
    def rc(self):
        return self.settings_service.get_setting(SETTINGS_E.RC)

    @rc.setter
    def rc(self, value):
        self.settings_service.set_setting(SETTINGS_E.RC, value)

    @property
    def sci(self):
        return self.settings_service.get_setting(SETTINGS_E.SCI)

    @sci.setter
    def sci(self, value):
        self.settings_service.set_setting(SETTINGS_E.SCI, value)

    @property
    def step(self):
        return self.settings_service.get_setting(SETTINGS_E.STEP)

    @step.setter
    def step(self, value):
        self.__logger.debug(f"Received call to set step to {value}")
        validated = validate_step(value)
        self.__logger.debug(f"Setting step to validated step {validated}")
        self.settings_service.set_setting(SETTINGS_E.STEP, validated)
        self.__logger.debug(f"Notifying observers of step change...{validated}")
        self.notify(ObserverEvents.DO_STEP_UPDATED, validated)

    @property
    def create_step_folder(self):
        return self.settings_service.get_setting(SETTINGS_E.CREATE_STEP_FOLDER)

    @create_step_folder.setter
    def create_step_folder(self, value):
        self.settings_service.set_setting(SETTINGS_E.CREATE_STEP_FOLDER, value)

    @property
    def auto_increment_step(self):
        return self.settings_service.get_setting(SETTINGS_E.AUTO_INCREMENT_STEP)

    @auto_increment_step.setter
    def auto_increment_step(self, value):
        self.settings_service.set_setting(SETTINGS_E.AUTO_INCREMENT_STEP, value)

    @property
    def step_no_index_delimiter(self):
        return self.settings_service.get_setting(SETTINGS_E.STEP_NO_INDEX_DELIMITER)

    @step_no_index_delimiter.setter
    def step_no_index_delimiter(self, value):
        self.settings_service.set_setting(SETTINGS_E.STEP_NO_INDEX_DELIMITER, value)

    @property
    def image_browser_geometry(self):
        return self.settings_service.get_setting(SETTINGS_E.IMAGE_BROWSER_GEOMETRY)

    @image_browser_geometry.setter
    def image_browser_geometry(self, value):
        self.settings_service.set_setting(SETTINGS_E.IMAGE_BROWSER_GEOMETRY, value)

    @property
    def main_window_geometry(self):
        return self.settings_service.get_setting(SETTINGS_E.MAIN_WINDOW_GEOMETRY)

    @main_window_geometry.setter
    def main_window_geometry(self, value):
        self.settings_service.set_setting(SETTINGS_E.MAIN_WINDOW_GEOMETRY, value)

    @property
    def app_window_name_list(self):
        return self.settings_service.get_setting(SETTINGS_E.APP_WINDOW_NAME_LIST)

    @property
    def selected_window_name(self):
        return self.settings_service.get_setting(SETTINGS_E.SELECTED_WINDOW_NAME)

    @selected_window_name.setter
    def selected_window_name(self, value):
        self.settings_service.update_window_list_setting(value)
        self.notify(ObserverEvents.RELOAD_PICS_FOLDER)
