# pylint: disable=missing-docstring,line-too-long

from core.observer import Observable
from core.enums import ApplicationSettingsEnum as SETTINGS_E
from core.enums import ObserverEvents
from core.logger import get_logger
from services.settings_service import SettingsService
from utils.validation import validate_step

logger = get_logger(__name__)


class SettingsViewModel(Observable):
    def __init__(self, settings_service: SettingsService):
        super().__init__()
        self.settings_service = settings_service

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
        if work_dir is not None:
            self.work_dir = work_dir
        if rc is not None:
            self.rc = rc
        if sci is not None:
            self.sci = sci
        if step is not None:
            self.step = step
        if create_step_folder is not None:
            self.create_step_folder = create_step_folder
        if auto_increment_step is not None:
            self.auto_increment_step = auto_increment_step
        if step_no_index_delimiter is not None:
            self.step_no_index_delimiter = step_no_index_delimiter
        if selected_window_name is not None:
            self.selected_window_name = selected_window_name
        if image_browser_geometry is not None:
            self.image_browser_geometry = image_browser_geometry
        if main_window_geometry is not None:
            self.main_window_geometry = main_window_geometry

    def increment_step(self):
        self.step += 1

    def decrement_step(self):
        self.step -= 1

    # ------------------------------------------------------------------
    # Settings state properties
    # ------------------------------------------------------------------

    @property
    def work_dir(self):
        return self.settings_service.get_setting(SETTINGS_E.work_dir)

    @work_dir.setter
    def work_dir(self, value):
        self.settings_service.set_setting(SETTINGS_E.work_dir, value)

    @property
    def rc(self):
        return self.settings_service.get_setting(SETTINGS_E.rc)

    @rc.setter
    def rc(self, value):
        self.settings_service.set_setting(SETTINGS_E.rc, value)

    @property
    def sci(self):
        return self.settings_service.get_setting(SETTINGS_E.sci)

    @sci.setter
    def sci(self, value):
        self.settings_service.set_setting(SETTINGS_E.sci, value)

    @property
    def step(self):
        return self.settings_service.get_setting(SETTINGS_E.step)

    @step.setter
    def step(self, value):
        validated = validate_step(value)
        self.settings_service.set_setting(SETTINGS_E.step, validated)
        self.notify(ObserverEvents.DO_STEP_UPDATED, validated)

    @property
    def create_step_folder(self):
        return self.settings_service.get_setting(SETTINGS_E.create_step_folder)

    @create_step_folder.setter
    def create_step_folder(self, value):
        self.settings_service.set_setting(SETTINGS_E.create_step_folder, value)

    @property
    def auto_increment_step(self):
        return self.settings_service.get_setting(SETTINGS_E.auto_increment_step)

    @auto_increment_step.setter
    def auto_increment_step(self, value):
        self.settings_service.set_setting(SETTINGS_E.auto_increment_step, value)

    @property
    def step_no_index_delimiter(self):
        return self.settings_service.get_setting(SETTINGS_E.step_no_index_delimiter)

    @step_no_index_delimiter.setter
    def step_no_index_delimiter(self, value):
        self.settings_service.set_setting(SETTINGS_E.step_no_index_delimiter, value)

    @property
    def image_browser_geometry(self):
        return self.settings_service.get_setting(SETTINGS_E.image_browser_geometry)

    @image_browser_geometry.setter
    def image_browser_geometry(self, value):
        self.settings_service.set_setting(SETTINGS_E.image_browser_geometry, value)

    @property
    def main_window_geometry(self):
        return self.settings_service.get_setting(SETTINGS_E.main_window_geometry)

    @main_window_geometry.setter
    def main_window_geometry(self, value):
        self.settings_service.set_setting(SETTINGS_E.main_window_geometry, value)

    @property
    def app_window_name_list(self):
        return self.settings_service.get_setting(SETTINGS_E.app_window_name_list)

    @property
    def selected_window_name(self):
        return self.settings_service.get_setting(SETTINGS_E.selected_window_name)

    @selected_window_name.setter
    def selected_window_name(self, value):
        self.settings_service.update_window_list_setting(value)
        self.notify(ObserverEvents.RELOAD_PICS_FOLDER)
