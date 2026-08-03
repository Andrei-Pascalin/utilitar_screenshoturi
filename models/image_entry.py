from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImageEntry:
    """
    Represents a single image available in the image browser.
    """

    file_path: Path
    file_name: str

    selected: bool = False