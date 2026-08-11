# pylint: disable=missing-docstring,line-too-long

import time
from pathlib import Path

from core.logger import get_logger
from core.enums import ApplicationSettingsEnum as SETTINGS_E

from services.settings_service import SettingsService
from utils.validation import sanitize_name


class ScreenshotPathService:
    def __init__(self):
        self.settings = SettingsService()
        self.logger = get_logger(__name__)

    def build_output_path(self):
        """Build and create the output path without renaming the existing first image yet."""
        work_dir = Path(self.settings.get_setting(SETTINGS_E.WORK_DIR))

        if not str(work_dir):
            raise ValueError("Work directory is required.")

        # Validate the raw user input first.
        raw_rc = self.settings.get_setting(SETTINGS_E.RC)
        raw_sci = self.settings.get_setting(SETTINGS_E.SCI)
        raw_step = self.settings.get_setting(SETTINGS_E.STEP)

        if raw_rc == "":
            raise ValueError("RC no. cannot be empty.")

        if raw_sci == "":
            raise ValueError("SCI no. cannot be empty.")

        # if not raw_step.isdigit() or int(raw_step) < 1:
        #     raise ValueError("Step no. must be a positive integer (>= 1).")

        # Sanitize only after validation.
        rc = sanitize_name(raw_rc)
        sci = sanitize_name(raw_sci)

        step_folder = f"Step{raw_step}"

        # Create step folder only if checkbox is enabled
        if self.settings.get_setting(SETTINGS_E.CREATE_STEP_FOLDER):
            folder = work_dir / rc / sci / step_folder
        else:
            # Create only the parent folders (RC/SCI) without the step folder
            folder = work_dir / rc / sci
        folder.mkdir(parents=True, exist_ok=True)


        # Find the next index for photos in this step
        step_number = int(raw_step)
        delimiter = self.settings.get_setting(SETTINGS_E.STEP_NO_INDEX_DELIMITER)
        prefix = f"step{step_number}{delimiter}"

        # Check for files without index (step1.png)
        file_without_index = folder / f"step{step_number}.png"

        # Search for existing indexed files with this pattern
        existing_indices = []
        first_image_name_changed = None
        if folder.exists():
            for file in folder.glob(f"{prefix}*.png"):
                try:
                    # Extract index from filename (step1.5.png -> 5)
                    index_str = file.stem.replace(prefix, "")
                    if index_str.isdigit():
                        existing_indices.append(int(index_str))
                except (ValueError, AttributeError):
                    pass

        # Determine the next index
        if not existing_indices and not file_without_index.exists():
            # First file - create without index
            filename = f"step{step_number}.png"
            destination = folder / filename
        else:
            # If we have more than one file, rename the first one (without index) to have .1 index
            if file_without_index.exists() and not existing_indices:
                # Prepare the rename but do it later, after capture completes.
                new_name_with_index = folder / f"{prefix}1.png"
                first_image_name_changed = (file_without_index, new_name_with_index)
                existing_indices.append(1)

            # Calculate next index
            next_index = max(existing_indices) + 1 if existing_indices else 2
            filename = f"{prefix}{next_index}.png"
            destination = folder / filename

        return (filename, destination, first_image_name_changed)

    def rename_first_image(self, first_image_name_changed) -> None:
        """Rename the original unindexed file after capture completes so UI refresh happens later."""
        source, destination = first_image_name_changed
        self._safe_rename(source, destination)

    #bleah... o alambicatura pentru a evita erorile de tipul "PermissionError: [WinError 32] The process cannot access the file because it is being used by another process"
    def _safe_rename(self, source: Path, destination: Path, retries: int = 5, delay: float = 0.2) -> None:
        last_error = None
        for attempt in range(retries):
            try:
                source.rename(destination)
                return
            except PermissionError as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                raise RuntimeError(
                    f"Could not rename '{source}' to '{destination}'. The file may be locked by another process."
                ) from exc
            except OSError as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                raise RuntimeError(
                    f"Could not rename '{source}' to '{destination}', error: {exc}"
                ) from exc
        if last_error is not None:
            raise RuntimeError(f"Could not rename '{source}' to '{destination}'. {last_error}") from last_error
