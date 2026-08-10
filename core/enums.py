from enum import StrEnum, auto


class CaptureMode(StrEnum):
    LEFT_MONITOR = auto()
    RIGHT_MONITOR = auto()
    WINDOW = auto()

# str mai jos e adaugat ca sa devina campurile string a.i. cand sunt accesate sa dea direct valoarea ca string
class ApplicationSettingsEnum(StrEnum):
     work_dir = auto()
     rc = auto()
     sci = auto()
     step = auto()
     create_step_folder = auto()
     auto_increment_step = auto()
     step_no_index_delimiter = auto()
     browser_visible = auto()
     app_window_name_list = auto()
     image_browser_geometry = auto()
     main_window_geometry = auto()
    #  selected_window_name = auto()

# Observer events
class ObserverEvents(StrEnum):
    DO_STEP_UPDATED = auto()
    DO_PREPARE_UI_CAPTURE = auto()
    DO_RESTORE_UI = auto()
    DO_INCREMENT_STEP = auto()
    DO_IMAGE_DELETED = auto()
    DO_IMAGE_ADDED = auto()
    REFRESH_FIRST_IMAGE_INDEX = auto()
    RELOAD_PICS_FOLDER = auto()
    NOTIFICATION = auto()
