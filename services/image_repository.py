# pylint: disable=missing-docstring,line-too-long

import re

from pathlib import Path
from services.notification_service import NotificationService
from services.settings_service import SettingsService
from models.image_entry import ImageEntry
from core.logger import get_logger
from core.enums import ApplicationSettingsEnum as SETTINGS_E
from utils.validation import get_img_entry_key_by_path, sanitize_name


logger = get_logger(__name__)

class ImageRepository:
    def __init__(self, settings_service:SettingsService, notification_service:NotificationService):
        self._pics_list = {}
        self._settings_service = settings_service
        self._notification_service = notification_service
        self._build_pics_list()

    def add_image(self, image:ImageEntry):
        self._pics_list[image.file_name] = image

    def get_image(self, name):
        return self._pics_list.get(name)

    def remove_image(self, path):
        img_entry_2_remove = get_img_entry_key_by_path(path, self._pics_list)
        self._pics_list.pop(img_entry_2_remove, None)

    def get_list(self)->list[ImageEntry]:
        return list(self._pics_list.values())

    def clear_repository(self):
        self._pics_list.clear()
        self._build_pics_list()

    def refresh_first_image_index(self, new_img_path:Path):
        old_key = f"step{self._settings_service.get_setting(SETTINGS_E.step)}.png"
        delimiter = self._settings_service.get_setting(SETTINGS_E.step_no_index_delimiter)
        new_key = f"step{self._settings_service.get_setting(SETTINGS_E.step)}{delimiter}1.png"
        new_value = ImageEntry(file_name=new_key, file_path=new_img_path)

        new_dict = {}
        for k, v in self._pics_list.items():
            if k == old_key:
                new_dict[new_key] = new_value
            else:
                new_dict[k] = v
        self._pics_list = new_dict

    def _build_pics_list(self)->None:
        work_dir = Path(self._settings_service.get_setting(SETTINGS_E.work_dir))
        raw_rc = self._settings_service.get_setting(SETTINGS_E.rc)
        raw_sci = self._settings_service.get_setting(SETTINGS_E.sci)

        if not raw_rc or not raw_sci:
            self._notification_service.error("Configuration", "RC and SCI names are required.")
            return

        # Sanitize the names using the shared helper
        rc = sanitize_name(raw_rc)
        sci = sanitize_name(raw_sci)

        # Build the SCI path
        sci_path = work_dir / rc / sci

        if not sci_path.exists():
            self._notification_service.error("Configuration", f"Path does not exist yet:\n{sci_path}")
            return

        # Recursively find all PNG files
        png_files = list(sci_path.glob("**/*.png"))

        # Custom sorting: by step number first, then by photo index
        def sort_key(file_path):
            """Extract step number and photo index for sorting from filename, with folder name fallback"""


            # Get the filename without extension
            file_stem = file_path.stem

            # Try to extract step number and index from filename
            # Pattern: step<number> or step<number>.<index>
            # Examples: step1, step1.1, step1.2, step2.3
            match = re.search(r'step(\d+)(?:\.(\d+))?', file_stem)

            if match:
                step_num = int(match.group(1))
                photo_index = int(match.group(2)) if match.group(2) else 0
                return (step_num, photo_index)

            # Fallback: try to extract step number from parent folder name
            parent_name = file_path.parent.name
            step_match = re.search(r'[Ss]tep(\d+)', parent_name)
            if step_match:
                step_num = int(step_match.group(1))
                return (step_num, 0)
            return (0, 0)

        sorted_files = sorted(png_files, key=sort_key)

        # smecherie cu tichie aicea jos
        self._pics_list = {
            img_path.name: ImageEntry(file_path=img_path, file_name=img_path.name)
            for img_path in sorted_files
        }
