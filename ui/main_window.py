# pylint: disable=missing-docstring,line-too-long

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from commands.capture_commands import CaptureWindowCommand, DecrementStepCommand, IncrementStepCommand, ReloadPicsCommand
from commands.zip_commands import CreateZipCommand
from core.constants import ICON_PATH
from core.enums import ApplicationSettingsEnum, ObserverEvents
from core.enums import CaptureMode
from core.logger import get_logger
from core.observer import IObserver
from services.notification_service import NotificationService, NotificationType
from viewmodels.capture_viewmodel import CaptureViewModel
from ui.tooltip import Tooltip
from ui.log_widget import ScreenshotLogWidget
from ui.browser_widget import BrowserWidget

logger = get_logger(__name__)

class ScreenshotObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
        if event is ObserverEvents.DO_IMAGE_ADDED:
            self._main_window.log_widget.add_entry(data)
            self._main_window.browser_widget.refresh_image_browser()

        elif event is ObserverEvents.DO_IMAGE_DELETED:
            self._main_window.log_widget.remove_entry(data)
            self._main_window.browser_widget.refresh_image_browser()

        elif event is ObserverEvents.REFRESH_FIRST_IMAGE_INDEX:
            self._main_window.log_widget.refresh_first_image_index(data)
            self._main_window.browser_widget.refresh_image_browser()

        elif event is ObserverEvents.RELOAD_PICS_FOLDER:
            self._main_window.log_widget.refresh_picture_logs()
            self._main_window.browser_widget.refresh_image_browser()

class UIReactObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
        if event is ObserverEvents.DO_PREPARE_UI_CAPTURE:
            self._main_window.save_left_button.config(state="disabled")
            self._main_window.save_right_button.config(state="disabled")
            # Hide GUI so it is not included in the screenshot.
            self._main_window.root.iconify()
        elif event is ObserverEvents.DO_RESTORE_UI:
            self._main_window.root.deiconify()
            self._main_window.save_left_button.config(state="normal")
            self._main_window.save_right_button.config(state="normal")

class StepObserver(IObserver):
    def __init__(self, main_window:MainWindow):
        super().__init__()
        self._main_window = main_window

    def update(self, event: str, data=None):
        if event is ObserverEvents.DO_STEP_UPDATED:
            self._main_window.step_var.set(data)
            logger.debug(f"MainWindow received STEP_UPDATED event. New step: {data}")
        elif event is ObserverEvents.DO_INCREMENT_STEP:
            try:
                current = int(self._main_window.step_var.get())
                logger.debug(f"DO INCREMENT STEP: {current + 1}")
                self._main_window.step_var.set(str(current + 1))
            except ValueError:
                self._main_window.step_var.set("1")

class NotificationObserver(IObserver):
    def update(self, event: str, data=None):
        logger.info(f"MainWindow received notification: {event}, data: {data}")
        # TODO maybe use own auto disappearing warning for info and warning messages, but for now just use messagebox
        # self.auto_dissapearing_warning("Notification", data, timeout=5000)
        if data.type == NotificationType.INFO:
            messagebox.showinfo(data.title, data.message)
        elif data.type == NotificationType.WARNING:
            messagebox.showwarning(data.title, data.message)
        elif data.type == NotificationType.ERROR:
            messagebox.showerror(data.title, data.message)

class MainWindow():

    def __init__(self, viewmodel:CaptureViewModel, notification_service:NotificationService):
        self.viewmodel = viewmodel
        self.notification_service = notification_service

        self.root = tk.Tk()

        self._create_variables()

        self._create_commands()

        self.create_gui()

        self._notification_receiver = NotificationObserver()
        self.notification_service.notification.add_observer(self._notification_receiver)

        self._step_change_receiver = StepObserver(self)
        self.viewmodel.add_observer(self._step_change_receiver)

        self._ui_react_receiver = UIReactObserver(self)
        self.viewmodel.add_observer(self._ui_react_receiver)

        self._screenshot_change_receiver = ScreenshotObserver(self)
        self.viewmodel.add_observer(self._screenshot_change_receiver)

        # Register a system-wide hotkey listener in background
        try:
            self.viewmodel.register_hotkeys(self.root)
        except Exception as e:
            logger.error(f"ERROR... HOTKEY: {e}")
            messagebox.showerror("Error", f'Failed to register system hotkey. Hotkey functionality will be disabled.\n\n{e}')

        self.root.bind("<Alt-z>", self.viewmodel.get_capture_shortcut_handler())


    def run(self):
        self.root.mainloop()

    def on_close(self):
        logger.debug("MainWindow.on_close called. Saving settings and closing application........")
        self.viewmodel.update_settings_from_ui(
            work_dir=self.work_dir_var.get(),
            rc=self.rc_var.get(),
            sci=self.sci_var.get(),
            step=int(self.step_var.get()),
            image_browser_geometry=self.browser_widget.get_normalised_geometry(),
            main_window_geometry=self.root.geometry(),
            window_name=self.app_window_name_var.get().strip(),
            create_step_folder=self.create_step_folder_var.get(),
            auto_increment_step=self.auto_increment_step_var.get(),
            step_no_index_delimiter=self.step_no_index_delimiter_var.get()
        )

        self.viewmodel.save_settings()
        self.root.destroy()

    def auto_dissapearing_warning(self, title, message, timeout=5000):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.transient(self.root)
        win.resizable(False, False)
        win.attributes("-topmost", True)

        ttk.Label(
            win,
            text=message,
            padding=15,
            justify="center"
        ).pack()

        # Center over parent
        win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

        win.after(timeout, win.destroy)


    def create_gui(self):
        """
        Build complete user interface.
        """
        # setăm pictograma ... ura ...
        self.root.iconbitmap(ICON_PATH)

        self.main_paned = ttk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL
        )

        self.main_paned.pack(
            fill="both",
            expand=True
        )

        self.left_frame = ttk.Frame(
            self.main_paned
        )

        self.main_paned.add(
            self.left_frame,
            weight=4
        )

        self.root.title("Utilitar screenshoturi...")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(5, weight=1)
        self.root.resizable(True, True)


        # ----------------------------------------------------
        # Browser widget
        # ----------------------------------------------------
        self.browser_widget = BrowserWidget(self)
        # self.browser_widget.frame.pack(fill="both", expand=True)



        # vcmd = (self.root.register(self.validate_step), "%P")
        vcmd = None

        PAD = 11
        frame_window_name = ttk.Frame(self.left_frame)
        frame_window_name.pack(fill="x", padx=PAD, pady=(PAD, 4))
        ttk.Label(frame_window_name, text="window name:").pack(side="left")

        # Combobox for window name with history
        window_name_combo = ttk.Combobox(
            frame_window_name,
            textvariable=self.app_window_name_var,
            values=self.window_name_list,
            width=60,
            state="normal"  # Allow editing while still showing dropdown
        )
        window_name_combo.pack(side="left", fill="x", expand=True, padx=(5, 0))


        # Work directory
        frame_work = ttk.Frame(self.left_frame)
        frame_work.pack(fill="x", padx=PAD, pady=(PAD, 4))

        ttk.Label(frame_work, text="work dir:").pack(side="left")

        ttk.Entry(
            frame_work,
            textvariable=self.work_dir_var,
            width=60
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        # RC / SCI
        frame_ids = ttk.Frame(self.left_frame)
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
        frame_step = ttk.Frame(self.left_frame)
        frame_step.pack(pady=4)


        ttk.Checkbutton(frame_step,
                        text="create step folder",
                        variable=self.create_step_folder_var,
                        ).grid(row=0, column=0, padx=5)

        ttk.Label(frame_step, text="step no.:").grid(row=0, column=1, padx=5)

        ttk.Entry(
            frame_step,
            textvariable=self.step_var,
            width=8,
            validate="key",
            validatecommand=vcmd,
        ).grid(row=0, column=2)

        # - / + step buttons
        frame_adjust = ttk.Frame(self.left_frame)
        frame_adjust.pack(fill="x", padx=PAD, pady=4)

        ttk.Button(
            frame_adjust,
            text="step-1",
            width=7,
            command=self.decrement_step_cmd
        ).pack(side="left")

        ttk.Checkbutton(self.root,
                        text="Auto increment step after save",
                        variable=self.auto_increment_step_var,
                        ).pack(anchor="w", padx=PAD, pady=(0, PAD))

        ttk.Button(
            frame_adjust,
            text="step+1",
            width=7,
            command=self.increment_step_cmd
        ).pack(side="right")

        # Save buttons
        frame_save = ttk.Frame(self.left_frame)
        frame_save.pack(fill="x", padx=PAD, pady=(4, PAD))

        frame_save.columnconfigure(0, weight=1)
        frame_save.columnconfigure(1, weight=1)
        frame_save.columnconfigure(2, weight=1)

        self.save_left_button = ttk.Button(
            frame_save,
            text="capture LEFT screen",
            width=20,
            command=lambda: self.capture_cmd(CaptureMode.LEFT_MONITOR)
        )

        self.save_window_button = ttk.Button(
            frame_save,
            text="capture WINDOW",
            width=20,
            command=lambda: self.capture_cmd(CaptureMode.WINDOW)
        )
        # Add tooltip to capture window button
        Tooltip(self.save_window_button, "Capture active window\nKeyboard: Win+Alt+Z")

        self.save_right_button = ttk.Button(
            frame_save,
            text="capture RIGHT screen",
            width=20,
            command=lambda: self.capture_cmd(CaptureMode.RIGHT_MONITOR)
        )
        self.save_left_button.grid(row=0, column=0, padx=5)
        self.save_window_button.grid(row=0, column=1, padx=5)
        self.save_right_button.grid(row=0, column=2, padx=5)

        # Refresh button and Create Zip button
        frame_refresh = ttk.Frame(self.left_frame)
        frame_refresh.pack(fill="x", padx=PAD, pady=(4, PAD))

        ttk.Button(
            frame_refresh,
            text="🔄 Reload Image Folder",
            command=self.reload_pics_list_cmd
        ).pack(side="left", fill="x", expand=False, padx=5)

        ttk.Button(
            frame_refresh,
            text="📦 Create ZIP",
            command=self.create_zip_cmd
        ).pack(side="left", fill="x", expand=False, padx=5)

        ttk.Button(
            frame_refresh,
            text="🖼 Images",
            command=self.browser_widget.toggle_visibility_image_browser_command
        ).pack(side="right", padx=5)

        # ----------------------------------------------------
        # Screenshot log
        # ----------------------------------------------------
        self.log_widget = ScreenshotLogWidget(self.left_frame, self)


        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.browser_widget.create_gui()
        self.root.update_idletasks()

        self.root.geometry(self.viewmodel.settings_service.get_setting(ApplicationSettingsEnum.main_window_geometry))

        # self.viewmodel.add_observer(self.browser_widget)
        # self.viewmodel.add_observer(self.log_widget)


    def update_browser_size(self, geometry):
        self.viewmodel.update_browser_size(geometry)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _create_variables(self):
        self.work_dir_var = tk.StringVar(value=self.viewmodel.settings_service.get_setting("work_dir"))
        self.rc_var = tk.StringVar(value=self.viewmodel.settings_service.get_setting("rc"))
        self.sci_var = tk.StringVar(value=self.viewmodel.settings_service.get_setting("sci"))
        self.step_var = tk.StringVar(value=self.viewmodel.settings_service.get_setting("step"))

        # Initialize window name from list or use default
        self.window_name_list = self.viewmodel.settings_service.get_setting("app_window_name_list")
        default_window_name = self.window_name_list[0] if self.window_name_list else "SMARTCataract DX"
        self.app_window_name_var = tk.StringVar(value=default_window_name)

        self.create_step_folder_var = tk.BooleanVar(value=self.viewmodel.settings_service.get_setting("create_step_folder"))
        self.auto_increment_step_var = tk.BooleanVar(value=self.viewmodel.settings_service.get_setting("auto_increment_step"))
        self.step_no_index_delimiter_var = tk.StringVar(value=self.viewmodel.settings_service.get_setting("step_no_index_delimiter"))

        self.step_var.trace_add("write", lambda *args: self.viewmodel.update_crt_step_from_ui(step=int(self.step_var.get()) if self.step_var.get().isdigit() else 1))
        self.rc_var.trace_add("write", lambda *args: self.viewmodel.update_rc(self.rc_var.get()))
        self.sci_var.trace_add("write", lambda *args: self.viewmodel.update_sci(self.sci_var.get()))
        self.work_dir_var.trace_add("write", lambda *args: self.viewmodel.update_work_dir(self.work_dir_var.get()))
        self.app_window_name_var.trace_add("write", lambda *args: self.viewmodel.update_app_window_name(self.app_window_name_var.get().strip()))
        self.auto_increment_step_var.trace_add("write", lambda *args: self.viewmodel.update_auto_increment_step())

    def _create_commands(self):
        self.capture_cmd = CaptureWindowCommand(self.viewmodel).execute
        self.reload_pics_list_cmd = ReloadPicsCommand(self.viewmodel).execute
        self.create_zip_cmd = CreateZipCommand(self.viewmodel).execute

        self.increment_step_cmd = IncrementStepCommand(self.viewmodel).execute
        self.decrement_step_cmd = DecrementStepCommand(self.viewmodel).execute
