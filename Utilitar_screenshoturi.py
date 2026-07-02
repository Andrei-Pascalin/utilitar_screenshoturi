#!/usr/bin/env python3

r"""
comanda de creare executabil cu nuitka:

de aici am aflat:
https://dev.to/weisshufer/from-pyinstaller-to-nuitka-convert-python-to-exe-without-false-positives-19jf

python -m nuitka --standalone --onefile --enable-plugin=tk-inter --windows-disable-console captare_ecran_teste.py
--windows-disable-console = e deprecated dar pe py 3.14 si nuitka 4.1.2 merge,
                            varianta moderna cu --windows-disable-console=disabled da eroare


comanda de creare cu nume diferit: (atentie trebuie adaugat pyton.exe la exceptii la windows defender)
python -m nuitka --standalone --onefile --enable-plugin=tk-inter --windows-disable-console --product-name="Utilitar_screenshoturi" --product-version="0.1" --output-filename="Utilitar_screenshoturi.exe" captare_ecran_teste.py

comanda de creare cu pyinstaller:
pyinstaller --onefile --windowed --name "Utilitar_Screenshoturi" captare_ecran_teste.py

***ultima folosita:
comanda finala de creare a executabilului cu nuitka, cu iconita personalizata, versiune produs, nume produs, companie, si includerea icoanei in date files ca sa fie disponibila la runtime pentru setarea iconitei ferestrei (altfel icoana e doar pentru fisierul EXE dar fereastra are iconita default python):
python -m nuitka --standalone --remove-output --include-data-files=camera_gear_icon.ico=camera_gear_icon.ico --enable-plugin=tk-inter --windows-disable-console --windows-icon-from-ico="C:\Liamis_testing\scripturi\utilitar_screenshoturi\camera_gear_icon.ico" --product-version="0.2" --product-name="Utilitar Screenshoturi" --output-filename="Utilitar_screenshoturi.exe" --company-name="AndreiP" Utilitar_screenshoturi.py


Descriere scurtă a capabilităților
- Capturează ecranul stâng, ecranul drept sau o fereastră activă a SCDX (sau alta specificata)
- Salvează imaginile în foldere structurate: work_dir\RC\SCI\STEP_X\step_X_1.
- Suport pentru incrementare automată a numărului de pas după salvare.
- Permite setarea RC, SCI, step și directorului de lucru din interfața GUI.
- Salvează setările în fișierul setari_utilitar_screenshoturi.json.
- Are hotkey global Win+Alt+U pentru captură rapidă ca sa nu dispara droddown-urile de la SCDX
- Afișează un log cu căi către imaginile salvate, cu butoane pentru a deschide locația în Explorer.
- Permite crearea unui fișier ZIP din conținutul folderului SCI, cu nume generat automat.
- Suportă o listă de nume de ferestre pentru captură, cu istoric în dropdown și validare după titlu parțial.
- Gestionează erorile și oferă mesaje informative utilizatorului.
- Asigură că doar o singură instanță a aplicației rulează simultan.
- Permite setarea unui delimitator personalizat între numărul pasului și indexul fotografiei în numele fișierelor (implicit ".") pentru compatibilitate cu diferite convenții de denumire.
"""


from logging import root
from logging import root
import re
import time
import argparse
import tkinter as tk
import json
import mss
import os
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk

# chestii de windows api
import win32gui
import win32con
from send2trash import send2trash

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
import tempfile

# Determine application directory for settings storage.
# When running as a frozen onefile (Nuitka/PyInstaller), prefer the
# directory containing the original executable (`sys.argv[0]`) so
# settings are written beside the EXE instead of the temporary
# extraction folder.
print(f"[DEBUG] sys.argv[0]: {sys.argv[0]}")
print(f"[DEBUG] __file__: {Path(__file__).parent}")
print (f"[DEBUG] sys.executable: {sys.executable}")

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
SETTINGS_FILE = APP_DIR / "setari_utilitar_screenshoturi.json"

# DEFAULT_WORK_DIR = Path.home() / "Liamis_testing"
DEFAULT_WORK_DIR = r"C:\Liamis_testing"

# Windows-forbidden filename characters:
# < > : " / \ | ? *
INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')

# Limit individual folder names to reduce path-length issues.
MAX_COMPONENT_LENGTH = 180

# declar chestia asta globala pt că eroare funcky de resize a ferestrei utilitarului
#  TODO: poate fi mutata in clasa MyCaptareEcranApp si sa fie self.sct
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


class LogWidget:
    """Custom log widget with buttons to open file explorer for each entry"""
    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.entries = []

        # Create main container frame
        self.container = tk.Frame(parent, bg="#f5f5f5")
        self.container.pack(fill="both", expand=True, padx=11, pady=(4, 11))

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.container, bg="#f5f5f5", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f5f5f5")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, pady=(10, 0))
        self.scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    def add_entry(self, path_str: str):
        """Add an entry with an open button and selectable text"""
        path = Path(path_str)

        # Main entry container with card-like design
        entry_frame = tk.Frame(self.scrollable_frame, bg="white", relief="flat", bd=0)
        entry_frame.pack(fill="x", padx=8, pady=4)

        # Add border/shadow effect using inner frame
        inner_frame = tk.Frame(entry_frame, bg="white")
        inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        def on_enter(event):
            """Hover effect"""
            inner_frame.config(bg="#f0f8ff")
            entry_frame.config(bg="#e8f4ff")

        def on_leave(event):
            """Restore normal state"""
            inner_frame.config(bg="white")
            entry_frame.config(bg="white")

        entry_frame.bind("<Enter>", on_enter)
        entry_frame.bind("<Leave>", on_leave)
        inner_frame.bind("<Enter>", on_enter)
        inner_frame.bind("<Leave>", on_leave)

        # Button container (left side)
        btn_frame = tk.Frame(inner_frame, bg="white")
        btn_frame.pack(side="left", padx=(5, 8), pady=6)

        def open_path():
            if path.exists():
                import subprocess
                try:
                    # Open file explorer and select the file
                    subprocess.Popen(f'explorer /select,"{path}"')
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open: {e}")
            else:
                messagebox.showwarning("Path not found", f"The path does not exist:\n{path_str}\n\nRefreshing log...")
                self.refresh_from_sci()

        btn = tk.Button(btn_frame, text="📁", command=open_path,
                       bg="#4CAF50", fg="white", font=("Times", 9, "bold"),
                       padx=10, pady=4, relief="flat", cursor="hand2",
                       activebackground="#45a049", activeforeground="white")
        btn.pack()

        # Text container (right side)
        text_frame = tk.Frame(inner_frame, bg="white")
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=4)

        # Create selectable text widget for the path
        text_widget = tk.Text(text_frame, height=2, wrap="word", bg="white",
                             fg="#333333", font=("Courier", 9), relief="flat",
                             cursor="ibeam", bd=0, padx=8, pady=6)
        text_widget.pack(fill="both", expand=True)

        # Insert the path text
        text_widget.insert("1.0", str(path_str))
        text_widget.config(state="disabled")  # Make read-only but selectable

        # Bind hover effects to text widget too
        text_widget.bind("<Enter>", on_enter)
        text_widget.bind("<Leave>", on_leave)

        self.entries.append((entry_frame, path_str))

    def clear(self):
        """Clear all entries from the log"""
        for entry_frame, _ in self.entries:
            entry_frame.destroy()
        self.entries.clear()

    def _update_scroll_region(self):
        """Update canvas scroll region and scroll to bottom"""
        # Force complete layout update
        self.scrollable_frame.update_idletasks()
        self.canvas.update_idletasks()

        # Update scrollregion with current bounding box
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

        # Update the parent window
        try:
            self.parent.update()
        except Exception:
            pass

        # Scroll to bottom using a more forceful method
        self.canvas.yview_scroll(999999, "units")

    def refresh_from_sci(self):
        """Refresh log by reading all PNG files from the SCI path"""
        self.clear()
        try:
            work_dir = Path(self.app.work_dir_var.get().strip())
            raw_rc = self.app.rc_var.get().strip()
            raw_sci = self.app.sci_var.get().strip()

            if not raw_rc or not raw_sci:
                messagebox.showwarning("Configuration", "RC and SCI names are required.")
                return

            # Sanitize the names using the app's method
            rc = self.app.sanitize_name(raw_rc)
            sci = self.app.sanitize_name(raw_sci)

            # Build the SCI path
            sci_path = work_dir / rc / sci

            if not sci_path.exists():
                messagebox.showinfo("Info", f"Path does not exist yet:\n{sci_path}")
                return

            # Recursively find all PNG files
            png_files = list(sci_path.glob("**/*.png"))

            # Custom sorting: by step number first, then by photo index
            def sort_key(file_path):
                """Extract step number and photo index for sorting from filename, with folder name fallback"""
                try:
                    # Get the filename without extension
                    file_stem = file_path.stem

                    # Try to extract step number and index from filename
                    # Pattern: step<number> or step<number>.<index>
                    # Examples: step1, step1.1, step1.2, step2.3
                    match = re.search(r'step(\d+)(?:\.(\d+))?', file_stem)

                    if match:
                        step_num = int(match.group(1))
                        photo_index = int(match.group(2)) if match.group(2) else 0
                        return (step_num, photo_index)

                    # Fallback: try to extract step number from parent folder name
                    parent_name = file_path.parent.name
                    step_match = re.search(r'[Ss]tep(\d+)', parent_name)
                    if step_match:
                        step_num = int(step_match.group(1))
                        return (step_num, 0)

                    return (0, 0)
                except Exception:
                    return (0, 0)

            png_files = sorted(png_files, key=sort_key)

            if png_files:
                for png_file in png_files:
                    self.add_entry(str(png_file))
                # Update scroll region after all entries are added
                self._update_scroll_region()
                messagebox.showinfo("Refresh complete", f"Found {len(png_files)} PNG file(s).")
            else:
                self.add_entry(f"No PNG files found in {sci_path}")
                self._update_scroll_region()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh: {e}")


class ImageBrowser:

    THUMB_W = 150
    THUMB_H = 120

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app

        self.image_paths = []

        self.visible_items = {}
        self.selected_path = None
        self.selected_index = None

        self.preview_photo = None

        self.original_image = None

        self.frame = ttk.Frame(parent)

        # -----------------------------
        # Top thumbnail area
        # -----------------------------

        top = ttk.Frame(self.frame)
        top.pack(fill="x")

        self.thumb_canvas = tk.Canvas(
            top,
            height=170,
            bg="white"
        )

        self.hscroll = ttk.Scrollbar(
            top,
            orient="horizontal",
            command=self._scroll_x
        )

        self.thumb_canvas.configure(
            xscrollcommand=self.hscroll.set
        )

        self.thumb_canvas.pack(
            fill="x",
            side="top"
        )

        self.hscroll.pack(
            fill="x",
            side="bottom"
        )

        # -----------------------------
        # Preview area
        # -----------------------------

        self.preview_frame = ttk.Frame(self.frame)
        self.preview_frame.pack(fill="both", expand=True)

        self.preview_canvas = tk.Canvas(
            self.preview_frame,
            bg="#f0f0f0",
            highlightthickness=0
        )

        self.preview_canvas.pack(
            fill="both",
            expand=True
        )

        self.preview_name = ttk.Label(
            self.preview_frame,
            text="",
            anchor="center"
        )

        self.preview_name.pack(
            fill="x",
            pady=(4, 6)
        )

        self.image_item = None

        self.preview_canvas.bind(
            "<Configure>",
            self.on_preview_resize
        )

        self.thumb_canvas.bind(
            "<Configure>",
            lambda e: self.update_visible_thumbnails()
        )

    def delete_image(self, path):

        if not messagebox.askyesno("Delete", f"Move\n\n{path.name}\n\nto the Recycle Bin?"):
            return

        try:
            send2trash(str(path))
            self.app.refresh_image_browser()
            self.app.refresh_log()
        except Exception as exc:
            messagebox.showerror( "Delete failed", str(exc) )

    def _scroll_x(self, *args):

        self.thumb_canvas.xview(*args)

        self.update_visible_thumbnails()

    def load_images(self, image_paths):

        self.image_paths = list(image_paths)

        for idx in list(self.visible_items):
            self.remove_thumbnail(idx)

        width = max(
            len(self.image_paths) * self.THUMB_W,
            1
        )

        self.thumb_canvas.configure(
            scrollregion=(0, 0, width, 170)
        )

        self.update_visible_thumbnails()

        if self.image_paths:
            self.select_image(
                self.image_paths[-1]
            )

    def update_visible_thumbnails(self):

        if not self.image_paths:
            return

        left = self.thumb_canvas.canvasx(0)

        right = (
            left +
            self.thumb_canvas.winfo_width()
        )

        first = max(
            0,
            int(left / self.THUMB_W) - 3
        )

        last = min(
            len(self.image_paths),
            int(right / self.THUMB_W) + 4
        )

        required = set(range(first, last))

        # remove old thumbnails

        for idx in list(self.visible_items):

            if idx not in required:
                self.remove_thumbnail(idx)

        # create or refresh visible thumbnails

        for idx in required:
            if idx not in self.visible_items:
                self.create_thumbnail(idx)
            else:
                self.update_thumbnail_style(idx)

    def remove_thumbnail(self, idx):

        item = self.visible_items.pop(idx, None)

        if not item:
            return

        self.thumb_canvas.delete(item["image"])
        self.thumb_canvas.delete(item["text"])
        self.thumb_canvas.delete(item["delete"])

    def _get_thumbnail_text_style(self, idx):
        if idx == self.selected_index:
            return "#058b9c", ("TkDefaultFont", 12, "bold", "italic")
        return "black", ("TkDefaultFont", 9)

    def update_thumbnail_style(self, idx):
        item = self.visible_items.get(idx)
        if not item:
            return

        fill, font = self._get_thumbnail_text_style(idx)
        self.thumb_canvas.itemconfigure(item["text"], fill=fill, font=font)

    def create_thumbnail(self, idx):
        path = self.image_paths[idx]

        try:
            img = Image.open(path)
            img.thumbnail(
                (
                    self.THUMB_H,
                    self.THUMB_H
                )
            )
            photo = ImageTk.PhotoImage(img)
            x = (
                idx * self.THUMB_W +
                self.THUMB_W // 2
            )
            image_id = self.thumb_canvas.create_image(
                x,
                60,
                image=photo
            )

            fill, font = self._get_thumbnail_text_style(idx)
            text_id = self.thumb_canvas.create_text(
                x,
                140,
                text=path.name,
                width=140,
                fill=fill,
                font=font
            )

            self.thumb_canvas.tag_bind(
                image_id,
                "<Button-1>",
                lambda e, p=path:
                self.select_image(p)
            )

            delete_id = self.thumb_canvas.create_text(
                x,
                158,
                text="❌ Delete",
                fill="red",
                font=("Segoe UI Emoji", 10, "bold")
            )

            self.thumb_canvas.tag_bind(
                delete_id,
                "<Button-1>",
                lambda e, p=path: self.delete_image(p)
            )

            self.visible_items[idx] = {
                "image": image_id,
                "text": text_id,
                "delete": delete_id,
                "photo": photo
            }
        except Exception as exc:
            print(exc)

    def on_preview_resize(self, event):
        self.update_preview_image()

    def update_preview_image(self):
        if self.original_image is None:
            return

        w = self.preview_canvas.winfo_width()
        h = self.preview_canvas.winfo_height()

        if w < 10 or h < 10:
            return

        img = self.original_image.copy()
        img.thumbnail(
            (w - 10, h - 10),
            Image.Resampling.LANCZOS
        )
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.image_item = self.preview_canvas.create_image(
            w // 2,
            h // 2,
            image=self.preview_photo
        )
        self.preview_canvas.tag_bind(
            self.image_item,
            "<Button-1>",
            self.open_external_viewer
        )

    def select_image(self, path):
        self.selected_path = path

        try:
            self.original_image = Image.open(path)
            self.preview_name.configure(
                text=path.name
            )
            self.update_preview_image()

        except Exception as exc:
            self.preview_canvas.delete("all")

            self.preview_canvas.create_text(
                20,
                20,
                anchor="nw",
                text=str(exc)
            )
            self.preview_name.configure(text="")
        else:
            try:
                self.selected_index = self.image_paths.index(path)
            except ValueError:
                self.selected_index = None
            self.update_visible_thumbnails()

    def open_external_viewer(self, event=None):
        if self.selected_path and self.selected_path.exists():
            os.startfile(self.selected_path)


class MyCaptareEcranApp:
    def __init__(self):
        self.root = None
        self.log_widget = None
        self.app_hwnd = None

        self.pics_list = []

        self._hotkey_thread = None
        self._hotkey_thread_id = None
        self._hotkey_registered = False

        self.work_dir_var = None
        self.rc_var = None
        self.sci_var = None
        self.step_var = None
        self.auto_increment_step_var = None
        self.create_step_folder_var = None
        self.app_window_name_var = None
        self.step_no_index_delimiter_var = None

        self.save_left_button = None
        self.save_right_button = None
        self.browser_window = None
        self._browser_window_geometry = None

        # setting variable ---------------------------
        self.settings = self.load_settings()
        self._browser_window_geometry = self._normalize_browser_geometry(
            self.settings.get("image_browser_geometry")
        )

        self.step_no_index_delimiter_var = self.settings.get("step_no_index_delimiter", ".")


    def create_gui(self):
        self.root = tk.Tk()

        self.browser_window = tk.Toplevel(self.root)
        self.browser_window.withdraw()
        self.browser_window.title("Images")
        self.browser_window.protocol("WM_DELETE_WINDOW", self.hide_image_browser)
        self.browser_window.rowconfigure(0, weight=1)
        self.browser_window.columnconfigure(0, weight=1)
        self.browser_window.bind("<Configure>", self._on_browser_window_configure)

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

        self.right_frame = ttk.Frame(
            self.browser_window,
            width=500
        )
        self.right_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.main_paned.add(
            self.left_frame,
            weight=4
        )

        self.root.title("Utilitar screenshoturi...")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(5, weight=1)
        self.root.resizable(True, True)

        self.work_dir_var = tk.StringVar(value=self.settings["work_dir"])
        self.rc_var = tk.StringVar(value=self.settings["rc"])
        self.sci_var = tk.StringVar(value=self.settings["sci"])
        self.step_var = tk.StringVar(value=self.settings["step"])

        # Initialize window name from list or use default
        window_name_list = self.settings.get("app_window_name_list", [])
        default_window_name = window_name_list[0] if window_name_list else "SMARTCataract DX"
        self.app_window_name_var = tk.StringVar(value=default_window_name)

        vcmd = (self.root.register(self.validate_step), "%P")

        PAD = 11
        frame_window_name = ttk.Frame(self.left_frame)
        frame_window_name.pack(fill="x", padx=PAD, pady=(PAD, 4))
        ttk.Label(frame_window_name, text="window name:").pack(side="left")

        # Replace Entry with Combobox for window name with history
        window_name_combo = ttk.Combobox(
            frame_window_name,
            textvariable=self.app_window_name_var,
            values=window_name_list,
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

        self.create_step_folder_var = tk.BooleanVar(value=self.settings.get("create_step_folder", True))
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
            validatecommand=vcmd
        ).grid(row=0, column=2)

        # - / +
        frame_adjust = ttk.Frame(self.left_frame)
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
        frame_save = ttk.Frame(self.left_frame)
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
        Tooltip(self.save_window_button, "Capture active window\nKeyboard: Win+Alt+Z")

        self.save_right_button = ttk.Button(
            frame_save,
            text="capture RIGHT screen",
            width=20,
            command=self.save_right_screen
        )
        self.save_left_button.grid(row=0, column=0, padx=5)
        self.save_window_button.grid(row=0, column=1, padx=5)
        self.save_right_button.grid(row=0, column=2, padx=5)

        # Refresh button and Create Zip button
        frame_refresh = ttk.Frame(self.left_frame)
        frame_refresh.pack(fill="x", padx=PAD, pady=(4, PAD))

        ttk.Button(
            frame_refresh,
            text="🔄 Refresh Log",
            command=self.refresh_pics_list
        ).pack(side="left", fill="x", expand=False, padx=5)

        ttk.Button(
            frame_refresh,
            text="📦 Create ZIP",
            command=self.create_sci_zip
        ).pack(side="left", fill="x", expand=False, padx=5)

        ttk.Button(
            frame_refresh,
            text="🖼 Images",
            command=self.toggle_visibility_image_browser
        ).pack(side="right", padx=5)

        # ----------------------------------------------------
        # Screenshot log
        # ----------------------------------------------------

        self.log_widget = LogWidget(self.left_frame, self)

        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # Register a system-wide hotkey listener in background
        try:
            self.register_system_hotkey()
        except Exception:
            # Non-fatal: if registration fails, continue without global hotkey
            pass
        # Keyboard shortcuts: Win+Alt+Z for capture window
        # Tk bindings don't accept a direct 'Win' modifier. Bind Alt+z and
        # verify the Windows key is held using GetAsyncKeyState.
        def _on_shortcut_alt_z(event):
            VK_LWIN = 0x5B
            VK_RWIN = 0x5C
            try:
                win_left = ctypes.windll.user32.GetAsyncKeyState(VK_LWIN) & 0x8000
                win_right = ctypes.windll.user32.GetAsyncKeyState(VK_RWIN) & 0x8000
            except Exception:
                win_left = win_right = 0

            if win_left or win_right:
                self.save_window()

        self.root.bind("<Alt-z>", _on_shortcut_alt_z)

        # self.browser = ImageBrowser(
        #     self.right_frame
        # )

        self.browser = ImageBrowser(
            self.right_frame,
            self
        )

        self.browser.frame.pack(
            fill="both",
            expand=True
        )
        self.browser_visible = False

        self.root.update_idletasks()
        if self._can_refresh_on_startup():
            self.root.after(250, self.refresh_pics_list)
        # +++++++++++++++++++++++++++++++++++++++++++
        ico = Path(__file__).parent / "camera_gear_icon.ico"
        self.root.iconbitmap(ico)
        self.root.mainloop()

        # self.refresh_log()
        # ============================end of gui creation

    def _can_refresh_on_startup(self) -> bool:
        try:
            work_dir = Path(self.work_dir_var.get().strip())
            rc = self.rc_var.get().strip()
            sci = self.sci_var.get().strip()
            return bool(work_dir and rc and sci)
        except Exception:
            return False

    def _normalize_browser_geometry(self, value):
        if isinstance(value, dict):
            width = value.get("width")
            height = value.get("height")
            x = value.get("x")
            y = value.get("y")
            if width and height:
                geometry = f"{int(width)}x{int(height)}"
                if x is not None and y is not None:
                    geometry += f"+{int(x)}+{int(y)}"
                return geometry
        return None

    def _save_browser_window_geometry(self):
        if not self.browser_window:
            return

        try:
            self._browser_window_geometry = self.browser_window.geometry()
            self.settings["image_browser_geometry"] = {
                "width": self.browser_window.winfo_width(),
                "height": self.browser_window.winfo_height(),
                "x": self.browser_window.winfo_rootx(),
                "y": self.browser_window.winfo_rooty(),
            }
            if self.root is not None and self.app_window_name_var is not None:
                self.save_settings()
        except Exception:
            pass

    def _on_browser_window_configure(self, event=None):
        if not self.browser_window or not self.browser_window.winfo_ismapped():
            return
        self._save_browser_window_geometry()

    def animate_sash(self, target=None):
        if not self.browser_window:
            return

        self.root.update_idletasks()
        self.browser_window.update_idletasks()

        if self.browser_visible:
            self._position_browser_window()
            self.browser.update_preview_image()

    def _position_browser_window(self):
        if not self.browser_window or not self.root.winfo_ismapped():
            return

        self.root.update_idletasks()
        self.browser_window.update_idletasks()

        if self._browser_window_geometry:
            self.browser_window.geometry(self._browser_window_geometry)
            return

        x = self.root.winfo_rootx() + self.root.winfo_width() + 8
        y = self.root.winfo_rooty()
        width = 520
        height = min(800, self.root.winfo_screenheight() - 40)

        if x + width > self.root.winfo_screenwidth():
            x = max(10, self.root.winfo_screenwidth() - width - 10)

        if y + height > self.root.winfo_screenheight():
            y = max(10, self.root.winfo_screenheight() - height - 10)

        self._browser_window_geometry = f"{width}x{height}+{x}+{y}"
        self.browser_window.geometry(self._browser_window_geometry)

    def hide_image_browser(self):
        if self.browser_window:
            self._save_browser_window_geometry()
            self.browser_window.withdraw()
        self.browser_visible = False

    def toggle_visibility_image_browser(self):
        if not self.browser_window:
            self.browser_window = tk.Toplevel(self.root)
            self.browser_window.withdraw()
            self.browser_window.title("Images")
            self.browser_window.transient(self.root)
            self.browser_window.protocol("WM_DELETE_WINDOW", self.hide_image_browser)
            self.browser_window.rowconfigure(0, weight=1)
            self.browser_window.columnconfigure(0, weight=1)
            self.right_frame = ttk.Frame(self.browser_window, width=500)
            self.right_frame.grid(row=0, column=0, sticky="nsew")
            self.browser = ImageBrowser(self.right_frame)
            self.browser.frame.pack(fill="both", expand=True)

        if self.browser_visible:
            self.hide_image_browser()
            return

        self._position_browser_window()
        self.browser_window.deiconify()
        self.browser_window.lift()
        self.browser_window.update_idletasks()
        self.browser_visible = True
        self.browser.update_preview_image()

    def refresh_image_browser(self):

        try:

            work_dir = Path(
                self.work_dir_var.get().strip()
            )

            rc = self.sanitize_name(
                self.rc_var.get().strip()
            )

            sci = self.sanitize_name(
                self.sci_var.get().strip()
            )

            sci_path = work_dir / rc / sci

            if not sci_path.exists():

                self.browser.load_images([])
                return

            png_files = []

            for p in sci_path.rglob("*.png"):
                png_files.append(p)

            png_files.sort()

            self.browser.load_images(
                png_files
            )

        except Exception as exc:
            print(exc)

    def load_settings(self):
        print(f"[DEBUG] Loading settings from {SETTINGS_FILE}")
        if SETTINGS_FILE.exists():
            try:
                with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                    settings = json.load(f)
                    # Handle backwards compatibility: convert old string format to list
                    if isinstance(settings.get("app_window_name"), str):
                        old_value = settings["app_window_name"]
                        settings["app_window_name_list"] = [old_value] if old_value else []
                        del settings["app_window_name"]
                    if "app_window_name_list" not in settings:
                        settings["app_window_name_list"] = []
                    return settings
            except Exception:
                print(f"[DEBUG] Failed to load settings from {SETTINGS_FILE}, using defaults.")

        return { "work_dir": str(DEFAULT_WORK_DIR),
                "rc": "",
                "sci": "",
                "step": "1",
                "auto_increment_step": False,
                "create_step_folder": True,
                "step_no_index_delimiter": ".",
                "app_window_name_list": [],
                "image_browser_geometry": None}

    def save_settings(self):
        print(f"[DEBUG] Saving settings to {SETTINGS_FILE}")
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as f:
                print(f"[DEBUG] Writing settings to {SETTINGS_FILE}")

                # Add current window name to the list if not already present
                current_window_name = self.app_window_name_var.get().strip()
                window_name_list = self.settings.get("app_window_name_list", [])
                if current_window_name and current_window_name not in window_name_list:
                    window_name_list.append(current_window_name)

                json.dump({"work_dir": self.work_dir_var.get(),
                            "rc": self.rc_var.get(),
                            "sci": self.sci_var.get(),
                            "step": self.step_var.get(),
                            "auto_increment_step": self.auto_increment_step_var.get(),
                            "create_step_folder": self.create_step_folder_var.get(),
                            "step_no_index_delimiter": self.step_no_index_delimiter_var,
                            "app_window_name_list": window_name_list,
                            "image_browser_geometry": self.settings.get("image_browser_geometry"),
                            },
                            f, indent=2)
        except Exception as exc:
            print(f"[DEBUG] Error: {exc}")
            # maybe print smth.


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
        VK_Z = 0x5A  # 'Z'
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

            print("[DEBUG hotkey] Registering Win+Alt+Z hotkey from listener thread...")
            if not user32_local.RegisterHotKey(None, HOTKEY_ID, MOD_WIN | MOD_ALT, VK_Z):
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
        """Append message to log widget"""
        self.log_widget.add_entry(message)
        self.log_widget._update_scroll_region()

    def refresh_pics_list(self):
        """Refresh the picture list by reading all PNG files from SCI path"""
        self.log_widget.refresh_from_sci()
        self.refresh_image_browser()

    def extract_sci_number(self, sci_name: str) -> str:
        """Extract the number from SCI name.

        Examples:
            'SCDX-1234' -> '1234'
            '1234' -> '1234'
            'SCI-0001-ABC' -> '0001'
        """
        # Try to extract any continuous sequence of digits
        match = re.search(r'\d+', sci_name)
        if match:
            return match.group()
        return "0000"

    def create_sci_zip(self):
        """Create a zip file from SCI folder contents.

        Zip file pattern: SCI-xxxx-{RC_name}.zip
        Location: RC directory
        """
        try:
            work_dir = Path(self.work_dir_var.get().strip())
            raw_rc = self.rc_var.get().strip()
            raw_sci = self.sci_var.get().strip()

            if not raw_rc or not raw_sci:
                messagebox.showwarning("Configuration", "RC and SCI names are required.")
                return

            # Sanitize names
            rc = self.sanitize_name(raw_rc)
            sci = self.sanitize_name(raw_sci)

            # Build paths
            rc_path = work_dir / rc
            sci_path = rc_path / sci

            if not sci_path.exists():
                messagebox.showerror("Error", f"SCI path does not exist:\n{sci_path}")
                return

            # Extract SCI number
            sci_number = self.extract_sci_number(raw_sci).zfill(4)  # pad with zeros to 4 digits

            # Create zip filename: SCI-xxxx-{RC_name}.zip
            zip_filename = f"SCI-{sci_number}-{rc}.zip"
            zip_path = rc_path / zip_filename

            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through all files in sci_path and add them to zip
                for file_path in sci_path.rglob('*'):
                    if file_path.is_file():
                        # Calculate relative path from sci_path
                        arcname = file_path.relative_to(sci_path)
                        zipf.write(file_path, arcname)

            messagebox.showinfo("Success", f"ZIP file created:\n{zip_path}")
            # print(f"[DEBUG] ZIP file created: {zip_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create ZIP file:\n{str(e)}")
            # print(f"[DEBUG] Error creating ZIP: {e}")

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

        step_folder = f"Step{raw_step}"


        # Create step folder only if checkbox is enabled
        if self.create_step_folder_var.get():
            folder = work_dir / rc / sci / step_folder
        else:
            # Create only the parent folders (RC/SCI) without the step folder
            folder = work_dir / rc / sci
        folder.mkdir(parents=True, exist_ok=True)


        # Find the next index for photos in this step
        step_number = int(raw_step)
        delimiter = self.step_no_index_delimiter_var.strip()
        prefix = f"step{step_number}{delimiter}"

        # Check for files without index (step1.png)
        file_without_index = folder / f"step{step_number}.png"

        # Search for existing indexed files with this pattern
        existing_indices = []
        if folder.exists():
            for file in folder.glob(f"{prefix}*.png"):
                try:
                    # Extract index from filename (step1.5.png -> 5)
                    index_str = file.stem.replace(prefix, "")
                    if index_str.isdigit():
                        existing_indices.append(int(index_str))
                except (ValueError, AttributeError):
                    pass

        # Determine the next index
        if not existing_indices and not file_without_index.exists():
            # First file - create without index
            filename = f"step{step_number}.png"
            destination = folder / filename
        else:
            # If we have more than one file, rename the first one (without index) to have .1 index
            if file_without_index.exists() and not existing_indices:
                # Rename step1.png to step1.1.png
                new_name_with_index = folder / f"{prefix}1.png"
                file_without_index.rename(new_name_with_index)
                existing_indices.append(1)

            # Calculate next index
            next_index = max(existing_indices) + 1 if existing_indices else 2
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

        # if window capture is requested, activate the target window first
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
            # initially set the monitor region to capture as the full monitor
            # and if only_window is True, adjust it to the client area of the target window
            # some computation is needed to only get the client area (interior) of the window,
            # excluding borders and title bar (SCDX has a bigger yet invisible custom window frame)
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
            # actually capture the screen region using mss which stands for "Multiple Screen Shots"
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
        self.refresh_image_browser()

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
    app = MyCaptareEcranApp()
    app.create_gui()


if __name__ == "__main__":
    main()
