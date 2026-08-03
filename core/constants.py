from pathlib import Path
import sys


# =============================================================================
# Application
# =============================================================================

APP_NAME = "Utilitar Screenshoturi"
APP_VERSION = "1.0.0"


# =============================================================================
# Files
# =============================================================================

SETTINGS_FILE = "setari_utilitar_screenshoturi.json"

SUPPORTED_IMAGE_EXTENSIONS = (
    ".png"
)


# =============================================================================
# Filename / Path
# =============================================================================

MAX_FILENAME_LENGTH = 255
MAX_COMPONENT_LENGTH = 100

DEFAULT_STEP = "001"

DEFAULT_STEP_DELIMITER = "."


# =============================================================================
# UI
# =============================================================================

DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800

DEFAULT_BROWSER_WIDTH = 500
DEFAULT_BROWSER_HEIGHT = 700


# =============================================================================
# Logging
# =============================================================================

LOG_INFO = "INFO"
LOG_WARNING = "WARNING"
LOG_ERROR = "ERROR"


# =============================================================================
# Resources
# =============================================================================

RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"

ICON_PATH = RESOURCE_DIR / "icons" / "camera_gear2.ico"

is_frozen = getattr(sys, "frozen", False)
exe_candidate = None
if sys.argv and Path(sys.argv[0]).exists():
    exe_candidate = Path(sys.argv[0])
    if exe_candidate.suffix.lower() == ".exe":
        is_frozen = True

if is_frozen:
    if exe_candidate is None:
        exe_candidate = Path(sys.executable)
    APP_DIR = exe_candidate.parent
    print(f"[DEBUG] Running as frozen executable, using {exe_candidate} for APP_DIR")
else:
    print(f"[DEBUG] Running as script, using __file__ for APP_DIR")
    APP_DIR = Path(__file__).parent
print(f"[DEBUG] Application directory: {APP_DIR}")
# SETTINGS_FILE = APP_DIR / "setari_utilitar_screenshoturi.json"
SETTINGS_FILE = RESOURCE_DIR / SETTINGS_FILE

# DEFAULT_WORK_DIR = Path.home() / "Liamis_testing"
DEFAULT_WORK_DIR = r"C:\Liamis_testing"

