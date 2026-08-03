# pylint: disable=missing-docstring,line-too-long

import send2trash

from core.enums import ObserverEvents
from core.logger import get_logger
from core.enums import CaptureMode
from core.observer import Observable
from core.enums import ApplicationSettingsEnum as SETTINGS_E
from models.image_entry import ImageEntry
from services.hotkey_service import HotkeyService
from services.image_repository import ImageRepository
from services.notification_service import NotificationService
from services.screenshot_path_service import ScreenshotPathService
from services.settings_service import SettingsService
from services.capture_service import CaptureService
from services.zip_service import ZipService


logger = get_logger(__name__)


class CaptureViewModel(Observable):
    def __init__(self,
                 settings_service: SettingsService,
                 capture_service: CaptureService,
                 image_repository: ImageRepository,
                 path_service:ScreenshotPathService,
                 zip_service: ZipService,
                 hotkey_service: HotkeyService,
                 notification_service: NotificationService):
        super().__init__()
        self.settings_service = settings_service
        self.capture_service = capture_service
        self.image_repository = image_repository
        self.path_service=path_service
        self.zip_service = zip_service
        self.hotkey_service = hotkey_service
        self.notification_service = notification_service

        # TODO maybe use this for image events instead of making the viewmodel observable,
        # TODO but for now it's simpler to just make the viewmodel observable
        # self.image_event = Observable()

    def zip_images(self):
        # Implement the logic to zip images using the zip service
        images = self.image_repository.get_list()
        try:
            if images:
                zip_path = self.zip_service.create_zip(images)
                logger.info(f"Images zipped to {zip_path}")
                self.notification_service.info("Zip", f"Images zipped to: {zip_path}")
            else:
                logger.info("No images to zip.")
        except RuntimeError as e:
            self.notification_service.error("Zip", f"{e}")

    def reload_pics(self):
        self.image_repository.clear_repository()
        self.notify(ObserverEvents.RELOAD_PICS_FOLDER)

    def get_capture_shortcut_handler(self):
        return self.hotkey_service.get_capture_shortcut_handler()

    def register_hotkeys(self, root):
        self.hotkey_service.register_system_hotkey(root, lambda: self.capture_img(CaptureMode.WINDOW))

    def save_settings(self):
        self.settings_service.save_settings()

    def increment_step(self):
        self.settings_service.increment_step()
        self.notify(ObserverEvents.DO_STEP_UPDATED, self.settings_service.get_setting("step"))

    def decrement_step(self):
        self.settings_service.decrement_step()
        self.notify(ObserverEvents.DO_STEP_UPDATED, self.settings_service.get_setting("step"))

    def delete_image(self, path):
        try:
            send2trash.send2trash(path)
            # TODO remove , not needed
            # self.app.cmd_refresh_pics_list()
        except (WindowsError, OSError) as exc:
            logger.exception("Failed to delete image: %s", exc)
            self.notification_service.error("Capture", f"Failed to delete image: {exc}")
        else:
            self.image_repository.remove_image(path)
            self.notify(ObserverEvents.DO_IMAGE_DELETED, data=path)

    def capture_img(self, source:CaptureMode):
        # determină numele fișierului
        img_name = img_path = None
        first_image_name_changed = False
        try:
            img_name, img_path, first_image_name_changed = self.path_service.build_output_path()
        except ValueError as e:
            logger.error(f"Failed to build output path: {e}")
            self.notification_service.error("Capture", f"Failed to build output path: {e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error while building output path: {e}")
            self.notification_service.error("Capture", f"Unexpected error while building output path: {e}")
            return

        # capturează și salvează imaginea
        self.notify(ObserverEvents.DO_PREPARE_UI_CAPTURE)

        try:
            if source is CaptureMode.WINDOW:
                self.capture_service.capture_window(img_path)
            else:
                self.capture_service.capture_monitor(source, img_path)
        except Exception as e:
            logger.exception(f"Capture failed: {e}")
            self.notification_service.error("Capture", f"Capture failed: {e}")
            return
        finally:
            self.notify(ObserverEvents.DO_RESTORE_UI)

        if first_image_name_changed:
            try:
                self.path_service.rename_first_image(first_image_name_changed)
            except RuntimeError as exc:
                logger.warning("Could not finalize filename ordering: %s", exc)
                self.notification_service.warning("Capture", f"Could not finalize filename ordering: {exc}")

        # if img_name:
        self.image_repository.add_image(ImageEntry(file_path=img_path, file_name=img_name, selected=None))

        if first_image_name_changed:
            self.image_repository.refresh_first_image_index(first_image_name_changed[1])

        # incrementează step (dacă este cazul de autoincrement)
        if self.settings_service.get_setting(SETTINGS_E.auto_increment_step):
            logger.info(f"Incrementing step: {self.settings_service.settings.auto_increment_step}")
            self.notify(ObserverEvents.DO_INCREMENT_STEP)
            self.settings_service.save_settings()

        # notify log and broswer because a new image was added
        self.notify(ObserverEvents.DO_IMAGE_ADDED, img_path)

        if first_image_name_changed:
            self.notify(ObserverEvents.REFRESH_FIRST_IMAGE_INDEX, first_image_name_changed)

    def get_image_list(self) -> list[ImageEntry]:
        return self.image_repository.get_list()

    # ------------------------------------------
    # observable methods
    # ------------------------------------------


    # ------------------------------------------
    # UPDATE METHODS triggered by the ui changes
    # ------------------------------------------

    def update_settings_from_ui(self,
                                work_dir,
                                rc,
                                sci,
                                step,
                                image_browser_geometry,
                                main_window_geometry,
                                window_name,
                                create_step_folder,
                                auto_increment_step,
                                step_no_index_delimiter):
        self.settings_service.set_setting(SETTINGS_E.work_dir, work_dir)
        self.settings_service.set_setting(SETTINGS_E.rc, rc)
        self.settings_service.set_setting(SETTINGS_E.sci, sci)
        self.settings_service.set_setting(SETTINGS_E.step, step)
        self.settings_service.set_setting(SETTINGS_E.create_step_folder, create_step_folder)
        self.settings_service.set_setting(SETTINGS_E.auto_increment_step, auto_increment_step)
        self.settings_service.set_setting(SETTINGS_E.step_no_index_delimiter, step_no_index_delimiter)
        self.settings_service.set_setting(SETTINGS_E.image_browser_geometry, image_browser_geometry)
        self.settings_service.set_setting(SETTINGS_E.main_window_geometry, main_window_geometry)
        self.settings_service.update_window_list_setting(window_name)

    def update_crt_step_from_ui(self, step):
        self.settings_service.set_setting(SETTINGS_E.step, step)

    def update_rc(self, rc):
        self.settings_service.set_setting(SETTINGS_E.rc, rc)

    def update_sci(self, sci):
        self.settings_service.set_setting(SETTINGS_E.sci, sci)

    def update_work_dir(self, work_dir):
        self.settings_service.set_setting(SETTINGS_E.work_dir, work_dir)

    def update_app_window_name(self, window_name):
        self.settings_service.update_window_list_setting(window_name)

    def update_auto_increment_step(self):
        self.settings_service.set_setting(SETTINGS_E.auto_increment_step,
                                          not self.settings_service.get_setting(SETTINGS_E.auto_increment_step))

    def update_browser_size(self, geometry):
        self.settings_service.set_setting(SETTINGS_E.image_browser_geometry,
                                          geometry)