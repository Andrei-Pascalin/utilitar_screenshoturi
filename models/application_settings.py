from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from core.constants import DEFAULT_WORK_DIR




@dataclass
class ApplicationSettings:
    """
    Persistent application settings.
    Mirrors the content of settings.json.
    """

    work_dir: str = DEFAULT_WORK_DIR
    rc: str = "RC01"
    sci: str = "sci_1"
    step: int = 1

    create_step_folder: bool = True
    auto_increment_step: bool = False
    step_no_index_delimiter: str = "."

    browser_visible: bool = False
    image_browser_geometry: Optional[str] = None

    app_window_name_list: List[str] = field(default_factory=list)
    selected_window_name: Optional[str] = ""
