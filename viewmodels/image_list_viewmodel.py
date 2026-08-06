# pylint: disable=missing-docstring,line-too-long

from core.enums import ObserverEvents
from core.logger import get_logger
from core.observer import Observable
from models.image_entry import ImageEntry
from services.image_repository import ImageRepository

logger = get_logger(__name__)


class ImageListViewModel(Observable):
    def __init__(self, image_repository: ImageRepository, capture_viewmodel):
        super().__init__()
        self.image_repository = image_repository
        self.capture_viewmodel = capture_viewmodel
        self.capture_viewmodel.add_observer(self)

    def get_image_list(self) -> list[ImageEntry]:
        return self.image_repository.get_list()

    def refresh(self):
        self.notify(ObserverEvents.RELOAD_PICS_FOLDER)

    def delete_image(self, path):
        self.image_repository.remove_image(path)
        self.notify(ObserverEvents.DO_IMAGE_DELETED, path)

    def update(self, event: str, data=None):
        if event in {
            ObserverEvents.DO_IMAGE_ADDED,
            ObserverEvents.DO_IMAGE_DELETED,
            ObserverEvents.REFRESH_FIRST_IMAGE_INDEX,
            ObserverEvents.RELOAD_PICS_FOLDER,
        }:
            self.notify(event, data)
