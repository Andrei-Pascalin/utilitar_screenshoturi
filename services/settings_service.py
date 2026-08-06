# pylint: disable=missing-docstring,line-too-long

import json

from core.constants import SETTINGS_FILE
from core.logger import get_logger
from core.constants import DEFAULT_WORK_DIR
from core.enums import ApplicationSettingsEnum as SETTINGS_E
from models.application_settings import ApplicationSettings
from utils.validation import validate_step


logger = get_logger(__name__)


class SettingsService:
    def __init__(self):
        self.settings:ApplicationSettings = ApplicationSettings()

    def get_setting(self, key:SETTINGS_E):
        logger.debug(f"Getting setting for key: {key}")
        logger.debug(f"Current settings: {getattr(self.settings, key, 'Key not found')}")
        return getattr(self.settings, key, 'Key not found')

    def set_setting(self, key:SETTINGS_E, value):
        logger.debug(f"Setting {key} to {value}")
        setattr(self.settings, key, value)

    def load_settings(self):
        logger.debug(f"Loading settings from {SETTINGS_FILE}")
        if SETTINGS_FILE.exists():
            try:
                with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                    settings = json.load(f)

                    app_window_name_list = settings.get(SETTINGS_E.app_window_name_list, [])
                    self.settings.app_window_name_list = app_window_name_list
                    self.settings.selected_window_name = settings.get(
                        SETTINGS_E.selected_window_name,
                        app_window_name_list[0] if app_window_name_list else ""
                    )

                    self.settings.auto_increment_step = settings.get(SETTINGS_E.auto_increment_step, False)
                    self.settings.create_step_folder = settings.get(SETTINGS_E.create_step_folder, True)
                    self.settings.step_no_index_delimiter = settings.get(SETTINGS_E.step_no_index_delimiter, ".")
                    self.settings.work_dir = settings.get(SETTINGS_E.work_dir, DEFAULT_WORK_DIR)
                    self.settings.rc = settings.get(SETTINGS_E.rc, "RC01")
                    self.settings.sci = settings.get(SETTINGS_E.sci, "sci_1")
                    self.settings.step = validate_step(settings.get(SETTINGS_E.step, 1))
                    self.settings.image_browser_geometry = settings.get(SETTINGS_E.image_browser_geometry, None)
                    self.settings.main_window_geometry = settings.get(SETTINGS_E.main_window_geometry, None)
            except (FileExistsError, FileNotFoundError, json.JSONDecodeError, FloatingPointError) as e:
                logger.warning(f"Failed to load settings {e}")
        return self.settings

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
        logger.debug(f"Saving settings to {SETTINGS_FILE}")
        logger.debug(f"Current settings: {self.settings}")
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as f:
                window_name_list = self.settings.app_window_name_list
                json.dump({"work_dir": self.settings.work_dir,
                            "rc": self.settings.rc,
                            "sci": self.settings.sci,
                            "step": self.settings.step,
                            "auto_increment_step": self.settings.auto_increment_step,
                            "create_step_folder": self.settings.create_step_folder,
                            "step_no_index_delimiter": self.settings.step_no_index_delimiter,
                            "app_window_name_list": window_name_list,
                            "selected_window_name": self.settings.selected_window_name,
                            "image_browser_geometry": self.settings.image_browser_geometry,
                            "main_window_geometry": self.settings.main_window_geometry},
                            f, indent=2)

        except (FileExistsError, FileNotFoundError, FloatingPointError) as e:
            logger.error(f"Failed to save settings {e}")


    def increment_step(self):
        logger.debug(f"Current step type: {type(self.settings.step)}")
        self.settings.step = self.settings.step + 1

    def decrement_step(self):
        self.settings.step = validate_step(self.settings.step - 1)
