from enum import StrEnum, auto


class CaptureMode(StrEnum):
    LEFT_MONITOR = auto()
    RIGHT_MONITOR = auto()
    WINDOW = auto()

# str mai jos e adaugat ca sa devina campurile string a.i. cand sunt accesate sa dea direct valoarea ca string
class ApplicationSettingsEnum(StrEnum):
    LOG_LEVEL = auto()
    WORK_DIR = auto()
    RC = auto()
    SCI = auto()
    STEP = auto()
    CREATE_STEP_FOLDER = auto()
    AUTO_INCREMENT_STEP = auto()
    STEP_NO_INDEX_DELIMITER = auto()
    BROWSER_VISIBLE = auto()
    APP_WINDOW_NAME_LIST = auto()
    IMAGE_BROWSER_GEOMETRY = auto()
    MAIN_WINDOW_GEOMETRY = auto()
    SELECTED_WINDOW_NAME = auto()

# Observer events
class ObserverEvents(StrEnum):
    DO_STEP_UPDATED = auto()
    DO_PREPARE_UI_CAPTURE = auto()
    DO_RESTORE_UI = auto()
    # DO_INCREMENT_STEP = auto()
    DO_IMAGE_DELETED = auto()
    DO_IMAGE_ADDED = auto()
    REFRESH_FIRST_IMAGE_INDEX = auto()
    RELOAD_PICS_FOLDER = auto()
    NOTIFICATION = auto()
