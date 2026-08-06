from __future__ import annotations

from core.enums import ObserverEvents
from core.observer import Observable
from models.image_entry import ImageEntry
from viewmodels.image_list_viewmodel import ImageListViewModel


class LogViewModel(Observable):
    def __init__(self, image_list_viewmodel: ImageListViewModel):
        super().__init__()
        self.image_list_viewmodel = image_list_viewmodel
        self.image_list_viewmodel.add_observer(self)

        self._entries: list[ImageEntry] = []
        self.refresh()

    def get_entries(self) -> list[ImageEntry]:
        return list(self._entries)

    def refresh(self):
        self._entries = self.image_list_viewmodel.get_image_list()
        self.notify(ObserverEvents.RELOAD_PICS_FOLDER)

    def format_entry_text(self, entry: ImageEntry) -> str:
        return str(entry.file_path)

    def delete_entry(self, path: str):
        self.image_list_viewmodel.delete_image(path)
        self.refresh()

    def update(self, event: str, data=None):
        if event in {
            ObserverEvents.DO_IMAGE_ADDED,
            ObserverEvents.DO_IMAGE_DELETED,
            ObserverEvents.REFRESH_FIRST_IMAGE_INDEX,
            ObserverEvents.RELOAD_PICS_FOLDER,
        }:
            self.refresh()
