# pylint: disable=missing-docstring,line-too-long
# ------------------------
# System-wide hotkey support
# ------------------------
import ctypes
import threading
import win32con

from core.logger import get_logger


class HotkeyService:
    def __init__(self):
        self.__logger = get_logger(__name__)
        self.root = None
        self.cmd_save_window = None
        self._hotkey_thread = None
        self._hotkey_thread_id = None
        self._hotkey_registered = False

    # Keyboard shortcuts: Win+Alt+Z for capture window
    # Tk bindings don't accept a direct 'Win' modifier. Bind Alt+z and
    # verify the Windows key is held using GetAsyncKeyState.
    def _on_shortcut_alt_z(self, event):
        self.__logger.debug(f"Received event: {event}")
        # pylint: disable=invalid-name
        VK_LWIN = 0x5B
        VK_RWIN = 0x5C
        try:
            win_left = ctypes.windll.user32.GetAsyncKeyState(VK_LWIN) & 0x8000
            win_right = ctypes.windll.user32.GetAsyncKeyState(VK_RWIN) & 0x8000
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.__logger.error(f"Error occurred while checking Win key state: {e}")
            win_left = win_right = 0

        if win_left or win_right:
            self.cmd_save_window()

    def get_capture_shortcut_handler(self):
        return lambda: self._on_shortcut_alt_z(None)

    def register_system_hotkey(self, root, cmd_save_window):
        self.cmd_save_window = cmd_save_window
        self.root = root
        # pylint: disable=invalid-name
        MOD_ALT = 0x0001
        MOD_WIN = 0x0008
        VK_Z = 0x5A  # 'Z'
        HOTKEY_ID = 1

        def _listener():
            try:
                self._hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.__logger.error(f"Error occurred while getting thread ID: {e}")
                self._hotkey_thread_id = None

            self.__logger.debug(f"Listener thread started (tid={self._hotkey_thread_id})")

            msg = ctypes.wintypes.MSG()
            user32_local = ctypes.windll.user32
            WM_HOTKEY = 0x0312

            self.__logger.debug("Registering Win+Alt+Z hotkey from listener thread...")
            if not user32_local.RegisterHotKey(None, HOTKEY_ID, MOD_WIN | MOD_ALT, VK_Z):
                self.__logger.error("RegisterHotKey failed in listener")
                return

            self._hotkey_registered = True
            self.__logger.debug("Hotkey registered (listener)")

            while True:
                ret = user32_local.GetMessageW(ctypes.byref(msg), None, 0, 0)
                self.__logger.debug(f"GetMessageW returned {ret}, msg={getattr(msg, 'message', None)}")
                if ret == 0:
                    self.__logger.debug("GetMessageW returned 0, exiting listener")
                    break
                if ret == -1:
                    self.__logger.debug("GetMessageW returned -1, error, exiting listener")
                    break

                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    self.__logger.debug(f"WM_HOTKEY received (wParam={msg.wParam})")
                    try:
                        self.__logger.debug("Scheduling save_window on GUI thread")
                        self.root.after(0, self.cmd_save_window)
                    # pylint: disable=broad-exception-caught
                    except Exception as e:
                        self.__logger.error(f"Failed to schedule save_window: {e}")

                user32_local.TranslateMessage(ctypes.byref(msg))
                user32_local.DispatchMessageW(ctypes.byref(msg))

            self.__logger.debug("Listener thread exiting, unregistering hotkey")
            try:
                user32_local.UnregisterHotKey(None, HOTKEY_ID)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.__logger.error(f"Error occurred while unregistering hotkey: {e}")

        t = threading.Thread(target=_listener, daemon=True)
        t.start()
        self._hotkey_thread = t

    def unregister_system_hotkey(self):
        """Unregister the hotkey and stop the listener thread."""
        if not self._hotkey_registered:
            return
        # pylint: disable=invalid-name
        HOTKEY_ID = 1
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey(None, HOTKEY_ID)
        self._hotkey_registered = False

        # post WM_QUIT to the listener thread to stop the GetMessage loop
        if self._hotkey_thread_id:
            try:
                self.__logger.debug(f"Posting WM_QUIT to thread id {self._hotkey_thread_id}")
                user32.PostThreadMessageW(self._hotkey_thread_id, win32con.WM_QUIT, 0, 0)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.__logger.error(f"Error occurred while posting WM_QUIT: {e}")
