# pylint: disable=missing-docstring,line-too-long
# pylint: disable=c-extension-no-member

import time
from pathlib import Path

import mss
import win32gui
import win32con
from PIL import Image

from core.enums import CaptureMode
from core.logger import get_logger
from services.notification_service import NotificationService
from services.settings_service import SettingsService


class CaptureService:
    """
    Performs the actual screenshot capture.

    Responsibilities:
        - activate target window (if needed)
        - capture monitor/window
        - save image to disk

    Does NOT:
        - access Tkinter
        - show dialogs
        - write logs
        - update UI
    """

    def __init__(self,
                 notification_service: NotificationService
                 ):
        self.__logger = get_logger(__name__)
        self.settings_service = SettingsService()
        self.notifications = notification_service
        self.sct = mss.MSS()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture_left_monitor(self, img_path) -> Path:
        """
        Capture left monitor.
        """
        monitor = self._get_left_monitor()

        return self._capture(monitor,img_path)

    def capture_right_monitor(self, img_path) -> Path:
        """
        Capture right monitor.
        """
        monitor = self._get_right_monitor()

        return self._capture(monitor,img_path)

    def capture_monitor(self, source:CaptureMode, img_path):
        try:
            if source is CaptureMode.LEFT_MONITOR:
                return self.capture_left_monitor(img_path)
            else:
                return self.capture_right_monitor(img_path)
        except RuntimeError as e:
            raise e

    def capture_window(self, img_path):
        try:
            app_hwnd = self._activate_window(self.settings_service.settings.selected_window_name)
        except RuntimeError as e:
            raise e

        time.sleep(0.2)

        # Use client area (interior) instead of window rect (which includes borders/titlebar)
        left, top, right, bottom = win32gui.GetClientRect(app_hwnd)
        # Convert client coordinates to screen coordinates
        pt = win32gui.ClientToScreen(app_hwnd, (left, top))
        left, top = pt
        pt = win32gui.ClientToScreen(app_hwnd, (right, bottom))
        right, bottom = pt

        region = {
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top,
        }
        try:
            self._capture(region, img_path)
        except RuntimeError as e:
            raise e

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _capture(self, region, img_path: Path) -> Path:

        try:
            # actually capture the screen region using mss which stands for "Multiple Screen Shots"
            shot = self.sct.grab(region)

            image = Image.frombytes(
                    "RGB",
                    shot.size,
                    shot.rgb
                )
            image.save(img_path)
        except Exception as e:
            self.__logger.exception(f"Capture image failed: {e}")
            raise RuntimeError(e) from e

    def _get_monitors(self):
        """Get list of monitors"""
        monitors = self.sct.monitors[1:]
        if not monitors:
            raise RuntimeError("No monitors detected.")
        return monitors

    def _get_left_monitor(self):
        """Get the leftmost monitor"""
        return min(self._get_monitors(), key=lambda m: m["left"])

    def _get_right_monitor(self):
        """Get the rightmost monitor"""
        return max(self._get_monitors(), key=lambda m: m["left"])

    def _activate_window(self, window_title):
        """Activate the target window"""
        all_windows = []
        def callback(hwnd, _):
            # pylint: disable=c-extension-no-member
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    all_windows.append(title)
        # pylint: disable=c-extension-no-member
        win32gui.EnumWindows(callback, None)
        # self.__logger.debug(f"[DEBUG] Found windows: {all_windows}")

        # hwnd = win32gui.FindWindow(None, window_title)
        hwnd = self._find_window(window_title)

        if hwnd == 0:
            raise RuntimeError(f'Window not found: "{window_title}"')

        placement = win32gui.GetWindowPlacement(hwnd)
        show_cmd = placement[1]

        if show_cmd == win32con.SW_SHOWMINIMIZED or show_cmd == win32con.SW_SHOWMINNOACTIVE:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            show_cmd = win32con.SW_RESTORE

        if show_cmd != win32con.SW_SHOWMAXIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

        foreground_hwnd = win32gui.GetForegroundWindow()
        if foreground_hwnd != hwnd:
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
        return hwnd

    # cautare partiala dupa nume, ca FindWindow e prea strict si
    # fereastra are un titlu cu spatii
    def _find_window(self, partial_title):
        """Find window by partial title"""
        result = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd)
            # self.__logger.debug(f"[DEBUG] Checking window: '{title}'")
            # self.__logger.debug(f"[DEBUG] Looking for: '{partial_title}'")
            if partial_title.lower() in title.lower():
                result.append(hwnd)

        win32gui.EnumWindows(callback, None)
        return result[0] if result else 0
