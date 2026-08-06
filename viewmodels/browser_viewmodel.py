from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.enums import ObserverEvents
from core.observer import Observable
from models.image_entry import ImageEntry
from viewmodels.image_list_viewmodel import ImageListViewModel
from viewmodels.settings_viewmodel import SettingsViewModel
from utils.validation import get_img_entry_index_by_path


@dataclass(frozen=True)
class BrowserItem:
    file_path: Path
    file_name: str
    is_selected: bool = False

    @property
    def label(self) -> str:
        return self.file_path.name


class BrowserViewModel(Observable):
    def __init__(self,
                 image_list_viewmodel: ImageListViewModel,
                 settings_viewmodel: SettingsViewModel):
        super().__init__()
        self.image_list_viewmodel = image_list_viewmodel
        self.settings_viewmodel = settings_viewmodel
        self.image_list_viewmodel.add_observer(self)

        self._items: list[BrowserItem] = []
        self._selected_path: Path | None = None
        self._selected_index: int | None = None
        self.refresh()

    @property
    def browser_geometry(self):
        return self.settings_viewmodel.image_browser_geometry

    @browser_geometry.setter
    def browser_geometry(self, value):
        self.settings_viewmodel.image_browser_geometry = value

    def refresh(self):
        image_entries = self.image_list_viewmodel.get_image_list()
        self._items = [self._create_item(entry) for entry in image_entries]
        self._selected_index = self._find_selected_index(self._selected_path)
        if self._selected_index is None and self._items:
            self.select_image(self._items[-1].file_path)

    def _create_item(self, entry: ImageEntry) -> BrowserItem:
        is_selected = entry.file_path == self._selected_path
        return BrowserItem(entry.file_path, entry.file_name, is_selected)

    def _find_selected_index(self, selected_path: Path | None) -> int | None:
        if selected_path is None:
            return None
        for index, item in enumerate(self._items):
            if item.file_path == selected_path:
                return index
        return None

    def get_items(self) -> list[BrowserItem]:
        return list(self._items)

    def get_selected_index(self) -> int | None:
        return self._selected_index

    def select_image(self, path: Path):
        if path == self._selected_path and self._selected_index is not None:
            return

        self._selected_path = path
        self._selected_index = self._find_selected_index(path)
        self._items = [BrowserItem(item.file_path, item.file_name, item.file_path == path)
                       for item in self._items]
        self.notify(ObserverEvents.REFRESH_FIRST_IMAGE_INDEX, (path, path))

    def format_item_label(self, item: BrowserItem) -> str:
        return item.label

    def is_selected(self, path: Path) -> bool:
        return self._selected_path == path

    def delete_image(self, path: Path):
        self.image_list_viewmodel.delete_image(path)
        if self._selected_path == path:
            self._selected_path = None
            self._selected_index = None
        self.refresh()

    def update(self, event: str, data=None):
        if event in {
            ObserverEvents.DO_IMAGE_ADDED,
            ObserverEvents.DO_IMAGE_DELETED,
            ObserverEvents.REFRESH_FIRST_IMAGE_INDEX,
            ObserverEvents.RELOAD_PICS_FOLDER,
        }:
            self.refresh()
