#!/usr/bin/env python3

import re
import time
import argparse
import tkinter as tk
import json
import mss
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from PIL import Image

# chestii de windows api
import win32gui
import win32con

# ========================== 1 singura instanta:
import ctypes
import threading
import sys

MUTEX_NAME = "Singleton_Utilitar_Screenshoturi"
# chiar asta este eroarea din windows ....
ERROR_ALREADY_EXISTS = 183
mutex = ctypes.windll.kernel32.CreateMutexW( None, False, MUTEX_NAME, )
if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    print("Application is already running.")
    sys.exit(0)

#==================================================

# ----------------------------------------------------
# Config stuff
# ----------------------------------------------------
# SETTINGS_FILE = Path("setari_utilitar_screenshoturi.json")

from pathlib import Path
import sys

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

SETTINGS_FILE = APP_DIR / "setari_utilitar_screenshoturi.json"

# DEFAULT_WORK_DIR = Path.home() / "Liamis_testing"
DEFAULT_WORK_DIR = r"C:\Liamis_testing"

# Windows-forbidden filename characters:
# < > : " / \ | ? *
INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')

# Limit individual folder names to reduce path-length issues.
MAX_COMPONENT_LENGTH = 180

#  eroare funcky de resize a ferestrei
sct = mss.MSS()


class Tooltip:
    """Simple tooltip widget for tkinter"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.on_enter)
        widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        if self.tooltip:
            return
        x = event.x_root + 10
        y = event.y_root + 10
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="lightyellow",
                        relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
        label.pack()

    def on_leave(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class MyCaptareEcranApp:
    def __init__(self):
        self.root = None
        self.log_text = None
        self.app_hwnd = None
        self._hotkey_thread = None
        self._hotkey_thread_id = None
        self._hotkey_registered = False

        self.work_dir_var = None
        self.rc_var = None
        self.sci_var = None
        self.step_var = None
        self.auto_increment_step_var = None
        self.app_window_name_var = None

        self.save_left_button = None
        self.save_right_button = None

        # setting variable ---------------------------
        self.settings = self.load_settings()


    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Utilitar screenshoturi...")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(5, weight=1)
        self.root.resizable(True, True)

        self.work_dir_var = tk.StringVar(value=self.settings["work_dir"])
        self.rc_var = tk.StringVar(value=self.settings["rc"])
        self.sci_var = tk.StringVar(value=self.settings["sci"])
        self.step_var = tk.StringVar(value=self.settings["step"])
        self.app_window_name_var = tk.StringVar(value="SMARTCataract DX")

        vcmd = (self.root.register(self.validate_step), "%P")

        PAD = 11
        frame_window_name = ttk.Frame(self.root)
        frame_window_name.pack(fill="x", padx=PAD, pady=(PAD, 4))
        ttk.Label(frame_window_name, text="window name:").pack(side="left")
        ttk.Entry(
            frame_window_name,
            textvariable=self.app_window_name_var,
            width=60
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))


        # Work directory
        frame_work = ttk.Frame(self.root)
        frame_work.pack(fill="x", padx=PAD, pady=(PAD, 4))

        ttk.Label(frame_work, text="work dir:").pack(side="left")

        ttk.Entry(
            frame_work,
            textvariable=self.work_dir_var,
            width=60
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        # RC / SCI
        frame_ids = ttk.Frame(self.root)
        frame_ids.pack(pady=4)

        ttk.Label(frame_ids, text="RC name:").grid(row=0, column=0, padx=5)
        ttk.Entry(
            frame_ids,
            textvariable=self.rc_var,
            width=25
        ).grid(row=0, column=1, padx=5)

        ttk.Label(frame_ids, text="SCI name:").grid(row=0, column=2, padx=5)
        ttk.Entry(
            frame_ids,
            textvariable=self.sci_var,
            width=45
        ).grid(row=0, column=3, padx=5)

        # Step
        frame_step = ttk.Frame(self.root)
        frame_step.pack(pady=4)

        ttk.Label(frame_step, text="step no.:").grid(row=0, column=0, padx=5)

        ttk.Entry(
            frame_step,
            textvariable=self.step_var,
            width=8,
            validate="key",
            validatecommand=vcmd
        ).grid(row=0, column=1)

        # - / +
        frame_adjust = ttk.Frame(self.root)
        frame_adjust.pack(fill="x", padx=PAD, pady=4)

        ttk.Button(
            frame_adjust,
            text="step-1",
            width=7,
            command=self.decrement_step
        ).pack(side="left")

        self.auto_increment_step_var = tk.BooleanVar(value=self.settings.get("auto_increment_step", True))
        ttk.Checkbutton(self.root,
                        text="Auto increment step after save",
                        variable=self.auto_increment_step_var,
                        ).pack(anchor="w", padx=PAD, pady=(0, PAD))

        ttk.Button(
            frame_adjust,
            text="step+1",
            width=7,
            command=self.increment_step
        ).pack(side="right")

        # Save buttons
        frame_save = ttk.Frame(self.root)
        frame_save.pack(fill="x", padx=PAD, pady=(4, PAD))

        frame_save.columnconfigure(0, weight=1)
        frame_save.columnconfigure(1, weight=1)
        frame_save.columnconfigure(2, weight=1)

        self.save_left_button = ttk.Button(
            frame_save,
            text="capture LEFT screen",
            width=20,
            command=self.save_left_screen
        )

        self.save_window_button = ttk.Button(
            frame_save,
            text="capture WINDOW",
            width=20,
            command=self.save_window
        )
        # Add tooltip to capture window button
        Tooltip(self.save_window_button, "Capture active window\nKeyboard: Win+Alt+U")

        self.save_right_button = ttk.Button(
            frame_save,
            text="capture RIGHT screen",
            width=20,
            command=self.save_right_screen
        )
        self.save_left_button.grid(row=0, column=0, padx=5)
        self.save_window_button.grid(row=0, column=1, padx=5)
        self.save_right_button.grid(row=0, column=2, padx=5)

        # ----------------------------------------------------
        # Screenshot log
        # ----------------------------------------------------

        self.log_text = ScrolledText(self.root, height=7, wrap="none")
        self.log_text.pack(fill="both", expand=True, padx=PAD, pady=(4, PAD))

        # Make the log read-only by default.
        self.log_text.config(state="disabled")

        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # Register a system-wide hotkey listener in background
        try:
            self.register_system_hotkey()
        except Exception:
            # Non-fatal: if registration fails, continue without global hotkey
            pass
        # Keyboard shortcuts: Win+Alt+U for capture window
        # Tk bindings don't accept a direct 'Win' modifier. Bind Alt+u and
        # verify the Windows key is held using GetAsyncKeyState.
        def _on_shortcut_alt_u(event):
            VK_LWIN = 0x5B
            VK_RWIN = 0x5C
            try:
                win_left = ctypes.windll.user32.GetAsyncKeyState(VK_LWIN) & 0x8000
                win_right = ctypes.windll.user32.GetAsyncKeyState(VK_RWIN) & 0x8000
            except Exception:
                win_left = win_right = 0

            if win_left or win_right:
                self.save_window()

        self.root.bind("<Alt-u>", _on_shortcut_alt_u)

        self.root.update_idletasks()
        self.root.mainloop()

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # maybe print smth..
                pass

        return { "work_dir": str(DEFAULT_WORK_DIR),
                "rc": "",
                "sci": "",
                "step": "1",
                "auto_increment_step": False,}

    def save_settings(self):
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as f:
                json.dump({"work_dir": self.work_dir_var.get(),
                            "rc": self.rc_var.get(),
                            "sci": self.sci_var.get(),
                            "step": self.step_var.get(),
                            "auto_increment_step": self.auto_increment_step_var.get(),
                            "app_window_name": self.app_window_name_var.get(),
                            },
                            f, indent=2)
        except Exception:
            # maybe print smth..
            pass

    def on_close(self):
        """Handle window close event"""
        # Unregister system hotkey and stop listener
        try:
            self.unregister_system_hotkey()
        except Exception:
            pass

        self.save_settings()
        self.root.destroy()

    # ------------------------
    # System-wide hotkey support
    # ------------------------
    def register_system_hotkey(self):
        MOD_ALT = 0x0001
        MOD_WIN = 0x0008
        VK_U = 0x55  # 'U'
        HOTKEY_ID = 1

        def _listener():
            try:
                self._hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            except Exception:
                self._hotkey_thread_id = None

            print(f"[DEBUG hotkey] Listener thread started (tid={self._hotkey_thread_id})")

            msg = ctypes.wintypes.MSG()
            user32_local = ctypes.windll.user32
            WM_HOTKEY = 0x0312

            print("[DEBUG hotkey] Registering Win+Alt+U hotkey from listener thread...")
            if not user32_local.RegisterHotKey(None, HOTKEY_ID, MOD_WIN | MOD_ALT, VK_U):
                print("[DEBUG hotkey] RegisterHotKey failed in listener")
                return

            self._hotkey_registered = True
            print("[DEBUG hotkey] Hotkey registered (listener)")

            while True:
                ret = user32_local.GetMessageW(ctypes.byref(msg), None, 0, 0)
                print(f"[DEBUG hotkey] GetMessageW returned {ret}, msg={getattr(msg, 'message', None)}")
                if ret == 0:
                    print("[DEBUG hotkey] GetMessageW returned 0, exiting listener")
                    break
                if ret == -1:
                    print("[DEBUG hotkey] GetMessageW returned -1, error, exiting listener")
                    break

                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    print(f"[DEBUG hotkey] WM_HOTKEY received (wParam={msg.wParam})")
                    try:
                        print("[DEBUG hotkey] Scheduling save_window on GUI thread")
                        self.root.after(0, self.save_window)
                    except Exception as e:
                        print("[DEBUG hotkey] Failed to schedule save_window:", e)

                user32_local.TranslateMessage(ctypes.byref(msg))
                user32_local.DispatchMessageW(ctypes.byref(msg))

            print("[DEBUG hotkey] Listener thread exiting, unregistering hotkey")
            try:
                user32_local.UnregisterHotKey(None, HOTKEY_ID)
            except Exception:
                pass

        t = threading.Thread(target=_listener, daemon=True)
        t.start()
        self._hotkey_thread = t

    def unregister_system_hotkey(self):
        """Unregister the hotkey and stop the listener thread."""
        if not self._hotkey_registered:
            return

        HOTKEY_ID = 1
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey(None, HOTKEY_ID)
        self._hotkey_registered = False

        # post WM_QUIT to the listener thread to stop the GetMessage loop
        if self._hotkey_thread_id:
            try:
                print(f"[DEBUG hotkey] Posting WM_QUIT to thread id {self._hotkey_thread_id}")
                user32.PostThreadMessageW(self._hotkey_thread_id, win32con.WM_QUIT, 0, 0)
            except Exception:
                pass

    # ============================================================
    # Utilities
    # ============================================================

    def activate_window(self, window_title):
        """Activate the target window"""
        # Debug: print all visible windows
        all_windows = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    all_windows.append(title)
        win32gui.EnumWindows(callback, None)
        # print(f"[DEBUG] Found windows: {all_windows}")

        # hwnd = win32gui.FindWindow(None, window_title)
        hwnd = self.find_window(window_title)

        if hwnd == 0:
            messagebox.showerror("Error", f'Nu am găsit fereastra "{window_title}"')
            return False

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

        self.app_hwnd = hwnd
        return True

    # cautare partiala dupa nume, ca FindWindow e prea strict si
    # fereastra are un titlu cu spatii
    def find_window(self, partial_title):
        """Find window by partial title"""
        result = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd)
            # print(f"[DEBUG] Checking window: '{title}'")
            # print(f"[DEBUG] Looking for: '{partial_title}'")
            if partial_title.lower() in title.lower():
                result.append(hwnd)

        win32gui.EnumWindows(callback, None)
        return result[0] if result else 0

    def append_log(self, message: str):
        """Append message to log text widget"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")  # Automatically scroll to newest entry.
        self.log_text.config(state="disabled")

    def sanitize_name(self, value: str) -> str:
        """Sanitize filename/folder names"""
        value = value.strip()
        value = INVALID_CHARS.sub("_", value)
        value = value.rstrip(" .")

        if not value:
            value = "_"

        return value[:MAX_COMPONENT_LENGTH]

    def get_monitors(self):
        """Get list of monitors"""
        monitors = sct.monitors[1:]
        if not monitors:
            raise RuntimeError("No monitors detected.")
        return monitors

    def get_left_monitor(self):
        """Get the leftmost monitor"""
        return min(self.get_monitors(), key=lambda m: m["left"])

    def get_right_monitor(self):
        """Get the rightmost monitor"""
        return max(self.get_monitors(), key=lambda m: m["left"])

    def validate_step(self, value):
        """Validate step number input"""
        if value == "":
            return True

        if value.isdigit():
            return int(value) >= 1
        return False

    def increment_step(self):
        """Increment step counter"""
        try:
            current = int(self.step_var.get())
        except ValueError:
            current = 1

        self.step_var.set(str(current + 1))

    def decrement_step(self):
        """Decrement step counter"""
        try:
            current = int(self.step_var.get())
        except ValueError:
            current = 1

        self.step_var.set(str(max(1, current - 1)))

    def build_output_path(self) -> Path:
        """Build and create output directory path"""
        work_dir = Path(self.work_dir_var.get().strip())

        if not str(work_dir):
            raise ValueError("Work directory is required.")

        # Validate the raw user input first.
        raw_rc = self.rc_var.get().strip()
        raw_sci = self.sci_var.get().strip()
        raw_step = self.step_var.get().strip()

        if raw_rc == "":
            raise ValueError("RC no. cannot be empty.")

        if raw_sci == "":
            raise ValueError("SCI no. cannot be empty.")

        if raw_step == "":
            raise ValueError("Step no. cannot be empty.")

        if not raw_step.isdigit() or int(raw_step) < 1:
            raise ValueError("Step no. must be a positive integer (>= 1).")

        # Sanitize only after validation.
        rc = self.sanitize_name(raw_rc)
        sci = self.sanitize_name(raw_sci)

        step_folder = f"step_{raw_step}"

        folder = work_dir / rc / sci / step_folder
        folder.mkdir(parents=True, exist_ok=True)

        # Find the next index for photos in this step
        step_number = int(raw_step)
        prefix = f"step{step_number}_"

        # Search for existing files with this pattern
        existing_indices = []
        if folder.exists():
            for file in folder.glob(f"{prefix}*.png"):
                try:
                    # Extract index from filename (step1_5.png -> 5)
                    index_str = file.stem.replace(prefix, "")
                    if index_str.isdigit():
                        existing_indices.append(int(index_str))
                except (ValueError, AttributeError):
                    pass

        # Calculate next index and if not exists return 1
        next_index = max(existing_indices) + 1 if existing_indices else 1
        filename = f"{prefix}{next_index}.png"
        destination = folder / filename

        return destination

    def capture(self, monitor, only_window=True):
        """Capture screenshot from monitor or window"""
        try:
            destination = self.build_output_path()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.save_left_button.config(state="disabled")
        self.save_right_button.config(state="disabled")

        # Hide GUI so it is not included in the screenshot.
        self.root.iconify()

        if only_window:
            window_name = self.app_window_name_var.get().strip()
            if window_name:
                if not self.activate_window(window_name):
                    self.root.deiconify()
                    self.save_left_button.config(state="normal")
                    self.save_right_button.config(state="normal")
                    return

        time.sleep(0.2)

        try:
            to_capture = monitor
            if only_window and self.app_hwnd:
                # Use client area (interior) instead of window rect (which includes borders/titlebar)
                left, top, right, bottom = win32gui.GetClientRect(self.app_hwnd)
                # Convert client coordinates to screen coordinates
                pt = win32gui.ClientToScreen(self.app_hwnd, (left, top))
                left, top = pt
                pt = win32gui.ClientToScreen(self.app_hwnd, (right, bottom))
                right, bottom = pt

                region = {
                    "left": left,
                    "top": top,
                    "width": right - left,
                    "height": bottom - top,
                }
                to_capture = region

            shot = sct.grab(to_capture)

            image = Image.frombytes(
                "RGB",
                shot.size,
                shot.rgb
            )

            image.save(destination)

        except Exception as exc:
            messagebox.showerror("Capture failed", str(exc))

        finally:
            self.root.deiconify()
            self.save_left_button.config(state="normal")
            self.save_right_button.config(state="normal")

        self.append_log(str(destination))

        if self.auto_increment_step_var.get():
            try:
                current = int(self.step_var.get())
                self.step_var.set(str(current + 1))
            except ValueError:
                self.step_var.set("1")

        self.save_settings()

    def save_left_screen(self):
        """Capture left screen"""
        self.capture(self.get_left_monitor(), only_window=False)

    def save_right_screen(self):
        """Capture right screen"""
        self.capture(self.get_right_monitor(), only_window=False)

    def save_window(self):
        """Capture active window"""
        self.capture(None, only_window=True)

# ============================================================
# GUI Initialization
# ============================================================

def main():
    """Main entry point"""
    # parser = argparse.ArgumentParser(description="Utilitar screenshoturi")
    # parser.add_argument("--capture-window", action="store_true", help="Capture active window and exit (headless)")
    # args = parser.parse_args()

    # if args.capture_window:
    #     run_cli_capture_window()
    #     return

    app = MyCaptareEcranApp()
    app.create_gui()


if __name__ == "__main__":
    main()


# def run_cli_capture_window():
#     """Run a single capture of the active window using saved settings and exit.

#     This creates a hidden Tk root so StringVar/BooleanVar work, avoids GUI
#     popups and prints the saved destination path to stdout.
#     """
#     app = MyCaptareEcranApp()

#     # Create a hidden root so tkinter variables work
#     root = tk.Tk()
#     root.withdraw()
#     app.root = root

#     # Setup variables from settings
#     settings = app.settings
#     app.work_dir_var = tk.StringVar(root, value=settings.get("work_dir", ""))
#     app.rc_var = tk.StringVar(root, value=settings.get("rc", ""))
#     app.sci_var = tk.StringVar(root, value=settings.get("sci", ""))
#     app.step_var = tk.StringVar(root, value=settings.get("step", "1"))
#     app.auto_increment_step_var = tk.BooleanVar(root, value=settings.get("auto_increment_step", False))
#     app.app_window_name_var = tk.StringVar(root, value=settings.get("app_window_name", ""))

#     # Minimal dummy buttons to satisfy calls to .config()
#     class _DummyBtn:
#         def config(self, **_):
#             return

#     app.save_left_button = _DummyBtn()
#     app.save_right_button = _DummyBtn()

#     # Replace append_log to print to stdout
#     app.append_log = lambda msg: print(msg)

#     # Find window
#     window_name = app.app_window_name_var.get().strip()
#     if not window_name:
#         print("No window name configured in settings.")
#         root.destroy()
#         return

#     hwnd = app.find_window(window_name)
#     if not hwnd:
#         print(f"Window not found: {window_name}")
#         root.destroy()
#         return

#     # Activate (maximize) the window before capture
#     try:
#         app.activate_window(window_name)
#     except Exception as e:
#         print("Failed to activate window:", e)

#     # Perform capture
#     app.capture(None, only_window=True)

#     root.destroy()
