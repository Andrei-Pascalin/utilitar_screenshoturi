# pylint: disable=missing-docstring,line-too-long
# pylint: disable=logging-fstring-interpolation

import json

from core.constants import SETTINGS_FILE
from core.constants import DEFAULT_WORK_DIR
from core.enums import ApplicationSettingsEnum as SETTINGS_E
from models.application_settings import ApplicationSettings
from utils.validation import validate_step


class SettingsService:
    __my_settings_instance = None
    __initialized = False

    def __new__(cls):
        if cls.__my_settings_instance is None:
            cls.__my_settings_instance = super().__new__(cls)
        return cls.__my_settings_instance

    def __init__(self):
        if self.__initialized:
            return

        self.__logger = None
        # Initialization happens only once ... singleton pattern monseniore ...
        self.settings:ApplicationSettings = ApplicationSettings()
        self.__initialized = True

    def set_logger(self, logger):
        self.__logger = logger

    def get_setting(self, key:SETTINGS_E):
        self.__logger.debug(f"Getting setting for key: {key}")
        self.__logger.debug(f"Current settings: {getattr(self.settings, key, 'Key not found')}")
        return getattr(self.settings, key, 'Key not found')

    def set_setting(self, key:SETTINGS_E, value):
        self.__logger.debug(f"Setting {key} to {value}")
        setattr(self.settings, key, value)

    def update_window_list_setting(self, current_window_name):
        window_name_list = self.settings.app_window_name_list
        if current_window_name:
            # Remove any entry that is a substring or superset of the current name
            window_name_list = [
                name for name in window_name_list
                if current_window_name not in name and name not in current_window_name
            ]
            # Add the current name to the top
            window_name_list.insert(0, current_window_name)
        self.settings.app_window_name_list = window_name_list
        self.settings.selected_window_name = current_window_name

    def save_settings(self):
        self.__logger.debug(f"Saving settings to {SETTINGS_FILE}")
        self.__logger.debug(f"Current settings: {self.settings}")
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as f:
                window_name_list = self.settings.app_window_name_list
                json.dump({"log_level": self.settings.log_level,
                            "work_dir": self.settings.work_dir,
                            "rc": self.settings.rc,
                            "sci": self.settings.sci,
                            "step": self.settings.step,
                            "auto_increment_step": self.settings.auto_increment_step,
                            "create_step_folder": self.settings.create_step_folder,
                            "step_no_index_delimiter": self.settings.step_no_index_delimiter,
                            "app_window_name_list": window_name_list,
                            "image_browser_geometry": self.settings.image_browser_geometry,
                            "main_window_geometry": self.settings.main_window_geometry},
                            f, indent=2)

        except (FileExistsError, FileNotFoundError, FloatingPointError) as e:
            self.__logger.error("Failed to save settings %s", e)

    def load_settings(self) -> None:
        self.__logger.debug("Loading settings from %s", SETTINGS_FILE)
        if SETTINGS_FILE.exists():
            try:
                with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                    settings = json.load(f, parse_float=float, parse_int=int)

                    if "app_window_name_list" not in settings:
                        settings.app_window_name_list = []

                    # read and return settings
                    self.settings.auto_increment_step = settings.get(SETTINGS_E.AUTO_INCREMENT_STEP, False)
                    self.settings.create_step_folder = settings.get(SETTINGS_E.CREATE_STEP_FOLDER, True)
                    self.settings.step_no_index_delimiter = settings.get(SETTINGS_E.STEP_NO_INDEX_DELIMITER, ".")
                    self.settings.work_dir = settings.get(SETTINGS_E.WORK_DIR, DEFAULT_WORK_DIR)
                    self.settings.rc = settings.get(SETTINGS_E.RC, "RC01")
                    self.settings.sci = settings.get(SETTINGS_E.SCI, "sci_1")
                    self.settings.step = validate_step(settings.get(SETTINGS_E.STEP, 1))
                    self.settings.app_window_name_list = settings.get(SETTINGS_E.APP_WINDOW_NAME_LIST, [])
                    self.settings.image_browser_geometry = settings.get(SETTINGS_E.IMAGE_BROWSER_GEOMETRY, None)
                    self.settings.main_window_geometry = settings.get(SETTINGS_E.MAIN_WINDOW_GEOMETRY, None)
                    self.settings.selected_window_name = self.settings.app_window_name_list[0]
                    self.settings.log_level = settings.get(SETTINGS_E.LOG_LEVEL, "INFO")
            except (FileExistsError, FileNotFoundError, FloatingPointError) as e:
                self.__logger.error("Failed to load settings %s", e)