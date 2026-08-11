# pylint: disable=missing-docstring,line-too-long

import send2trash

from core.enums import ObserverEvents
from core.logger import get_logger
from core.enums import CaptureMode
from core.observer import Observable
from models.image_entry import ImageEntry
from services.hotkey_service import HotkeyService
from services.image_repository import ImageRepository
from services.notification_service import NotificationService
from services.screenshot_path_service import ScreenshotPathService
from services.capture_service import CaptureService
from services.zip_service import ZipService
from viewmodels.settings_viewmodel import SettingsViewModel


class CaptureViewModel(Observable):
    def __init__(self,
                 settings_viewmodel: SettingsViewModel,
                 capture_service: CaptureService,
                 image_repository: ImageRepository,
                 path_service:ScreenshotPathService,
                 zip_service: ZipService,
                 hotkey_service: HotkeyService,
                 notification_service: NotificationService):
        super().__init__()
        self.settings_viewmodel = settings_viewmodel
        self.__logger = get_logger(__name__)
        self.capture_service = capture_service
        self.image_repository = image_repository
        self.path_service=path_service
        self.zip_service = zip_service
        self.hotkey_service = hotkey_service
        self.notification_service = notification_service

    def zip_images(self):
        # Implement the logic to zip images using the zip service
        images = self.image_repository.get_list()
        try:
            if images:
                zip_path = self.zip_service.create_zip(images)
                self.__logger.info(f"Images zipped to {zip_path}")
                self.notification_service.info("Zip", f"Images zipped to: {zip_path}")
            else:
                self.__logger.info("No images to zip.")
        except RuntimeError as e:
            self.notification_service.error("Zip", f"{e}")

    def reload_pics(self):
        self.image_repository.clear_repository()
        self.notify(ObserverEvents.RELOAD_PICS_FOLDER)

    def get_capture_shortcut_handler(self):
        return self.hotkey_service.get_capture_shortcut_handler()

    def register_hotkeys(self, root):
        self.hotkey_service.register_system_hotkey(root, lambda: self.capture_img(CaptureMode.WINDOW))

    def unregister_hotkeys(self):
        self.hotkey_service.unregister_system_hotkey()

    def delete_image(self, path):
        try:
            send2trash.send2trash(path)
        except (WindowsError, OSError) as exc:
            self.__logger.exception("Failed to delete image: %s", exc)
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
            self.__logger.error(f"Failed to build output path: {e}")
            self.notification_service.error("Capture", f"Failed to build output path: {e}")
            return
        except RuntimeError as e:
            self.__logger.error(f"Unexpected error while building output path: {e}")
            self.notification_service.error("Capture", f"Unexpected error while building output path: {e}")
            return

        # capturează și salvează imaginea
        self.notify(ObserverEvents.DO_PREPARE_UI_CAPTURE)

        try:
            if source is CaptureMode.WINDOW:
                self.capture_service.capture_window(img_path)
            else:
                self.capture_service.capture_monitor(source, img_path)
        except RuntimeError as e:
            self.__logger.exception(f"Capture failed: {e}")
            self.notification_service.error("Capture", f"Capture failed: {e}")
            return
        finally:
            self.notify(ObserverEvents.DO_RESTORE_UI)

        if first_image_name_changed:
            try:
                self.path_service.rename_first_image(first_image_name_changed)
            except RuntimeError as exc:
                self.__logger.warning("Could not finalize filename ordering: %s", exc)
                self.notification_service.warning("Capture", f"Could not finalize filename ordering: {exc}")

        # if img_name:
        self.image_repository.add_image(ImageEntry(file_path=img_path, file_name=img_name, selected=None))

        if first_image_name_changed:
            self.image_repository.refresh_first_image_index(first_image_name_changed[1])

        # incrementează step (dacă este cazul de autoincrement)
        if self.settings_viewmodel.auto_increment_step:
            self.__logger.info("Incrementing step because auto_increment_step is enabled")
            self.settings_viewmodel.increment_step()
            self.settings_viewmodel.save_settings()

        # notify log and browser because a new image was added
        self.notify(ObserverEvents.DO_IMAGE_ADDED, img_path)

        if first_image_name_changed:
            self.notify(ObserverEvents.REFRESH_FIRST_IMAGE_INDEX, first_image_name_changed)

    def get_image_list(self) -> list[ImageEntry]:
        return self.image_repository.get_list()
