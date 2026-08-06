from __future__ import annotations
from typing import TYPE_CHECKING

import re

from core.logger import get_logger

if TYPE_CHECKING:
    from models.image_entry import ImageEntry

# Windows-forbidden filename characters:
# < > : " / \ | ? *
INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')

# Limit individual folder names to reduce path-length issues.
MAX_COMPONENT_LENGTH = 180

logger = get_logger(__name__)

def sanitize_name(value: str) -> str:
    """Sanitize filename/folder names"""
    value = value.strip()
    value = INVALID_CHARS.sub("_", value)
    value = value.rstrip(" .")

    if not value:
        value = "_"

    return value[:MAX_COMPONENT_LENGTH]


def validate_step(value):
    """Validate step number input"""
    if isinstance(value, str):
        if not value.isdigit():
            return 1
        value = int(value)

    if value < 1:
        return 1
    return value

def extract_sci_number(sci_name: str) -> str:
    """Extract the number from SCI name.

    Examples:
        'SCDX-1234' -> '1234'
        '1234' -> '1234'
        'SCI-0001-ABC' -> '0001'
    """
    # Try to extract any continuous sequence of digits
    match = re.search(r'\d+', sci_name)
    if match:
        return match.group()
    return "0000"

def get_img_entry_key_by_path(path, imageEntries:dict[ImageEntry]) -> str:
    # next(((k, v) for k, v in imageEntries.items() if path in v.file_path), None)
    for key, value in imageEntries.items():
        logger.debug(f"get_img_entry_key_by_path: key={key}, value={value}, path={path}")
        if path == value.file_path:
            return key
    return None

def get_img_entry_index_by_path(path, imageEntries:list[ImageEntry]) -> int:
    matches = [i for i, img_entry in enumerate(imageEntries) if img_entry.file_path == path]
    return matches[0] if matches else None