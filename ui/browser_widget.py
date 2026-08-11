# pylint: disable=missing-docstring,line-too-long

from __future__ import annotations
from typing import TYPE_CHECKING

import os
import tkinter as tk

from tkinter import ttk
from PIL import Image, ImageTk

from core.enums import ObserverEvents
from core.logger import get_logger
from core.observer import IObserver
from utils.validation import get_img_entry_index_by_path

# ca sa evit circular import cand vreau sa specific tipul unui obiect sau returnul unei fncții
if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from models.image_entry import ImageEntry

# TODO aista are nevoie de ceva review mai serios, fac cam multă vrăjeala pe ici pe colo
# TODO imbunatatire:
# TODO 1. trimit doar root-ul din main_window, rezolv poate si eventualele dependinte circulare
# TODO 2. adaug un viewmodel separat poate pentru imagini sau trimit ca param si capture_viewmodel ca sa nu folosesc din main_window
class BrowserWidget(IObserver):
    """
    Displays captured images and allows basic navigation.
    """

    THUMB_W = 150
    THUMB_H = 120

    def __init__(self, app:MainWindow):
        self.__logger = get_logger(__name__)
        self._app = app

        self._browser_visible = False

        self.__browser_window = tk.Toplevel(self._app.root)
        self.__browser_window.withdraw()
        self.__browser_window.title("Images")
        self.__browser_window.transient(self._app.root)
        self.__browser_window.protocol("WM_DELETE_WINDOW", self._hide_image_browser)
        self.__browser_window.rowconfigure(0, weight=1)
        self.__browser_window.columnconfigure(0, weight=1)
        self.__browser_window.bind("<Configure>", self._on_browser_window_configure)

        self._browser_window_geometry = self._app.settings_vm.image_browser_geometry

        self._image_paths:list[ImageEntry] = self._app.capture_vm.get_image_list()

        self._visible_items = {}
        self._selected_path = None
        self._selected_index = None

        self._thumb_canvas = None
        self._hscroll = None
        self._preview_frame = None
        self._preview_canvas = None

        self._large_thumb_photo = None

        self._original_image = None
        self._frame = None

        self._image_item = None
        self._large_thumb_label = None

    def create_gui(self):
        # self.parent = parent
        self.__browser_window.geometry(self._browser_window_geometry)
        self._frame = ttk.Frame(self.__browser_window)

        # -----------------------------
        # Top thumbnail area
        # -----------------------------

        top = ttk.Frame(self._frame)
        top.pack(fill="x")

        self._thumb_canvas = tk.Canvas(
            top,
            height=170,
            bg="white"
        )

        self._hscroll = ttk.Scrollbar(
            top,
            orient="horizontal",
            command=self._scroll_x
        )

        self._thumb_canvas.configure(
            xscrollcommand=self._hscroll.set
        )

        self._thumb_canvas.pack(
            fill="x",
            side="top"
        )

        self._hscroll.pack(
            fill="x",
            side="bottom"
        )

        # -----------------------------
        # Preview area
        # -----------------------------

        self._preview_frame = ttk.Frame(self._frame)
        self._preview_frame.pack(fill="both", expand=True)

        self._large_thumb_canvas = tk.Canvas(
            self._preview_frame,
            bg="#f0f0f0",
            highlightthickness=0
        )

        self._large_thumb_canvas.pack(
            fill="both",
            expand=True
        )

        self._large_thumb_label = ttk.Label(
            self._preview_frame,
            text="",
            anchor="center",
            foreground="#058b9c",
            font=("TkDefaultFont", 14, "bold", "italic")
        )

        self._large_thumb_label.pack(
            fill="x",
            pady=(4, 6)
        )

        self._large_thumb_canvas.bind(
            "<Configure>",
            self._on_preview_resize
        )

        self._thumb_canvas.bind(
            "<Configure>",
            # lambda e: self._update_visible_thumbnails()
            lambda e: self._thumb_canvas.after_idle(self._update_visible_thumbnails)
        )

        self._frame.pack(fill="both", expand=True)

        if self._image_paths:
            self._select_image(self._image_paths[-1].file_path)

    # TODO this is not used, yet,the add_observer() call is commented out
    # TODO maybe use it in the future
    def update(self, event: str, data=None):
        # print("===================update")
        if event is ObserverEvents.DO_IMAGE_DELETED:
            self.refresh_image_browser()
        elif event is ObserverEvents.DO_IMAGE_ADDED:
            self.refresh_image_browser()

    def get_normalised_geometry(self):
        return self._browser_window_geometry

    def toggle_visibility_image_browser_command(self):
        if self._browser_visible:
            self._hide_image_browser()
            return
        self._position_browser_window()

        self.__browser_window.deiconify()
        self.__browser_window.lift()
        self.__browser_window.update_idletasks()
        self._browser_visible = True
        self._update_preview_image()

        # self.refresh_image_browser()
        self._update_thumb_scrollregion()
        # width = max(len(self._image_paths) * self.THUMB_W, 1)
        # self._thumb_canvas.configure(scrollregion=(0, 0, width, 170))
        # self._update_visible_thumbnails()

        self._thumb_canvas.after_idle(self._update_visible_thumbnails)
        if self._image_paths:
            self._select_image(self._image_paths[-1].file_path)

    # this method refreshes the browser image thumb previews, so it does not do any folder walking
    # it is simple enough so adding or removing functions are redundant
    def refresh_image_browser(self):
        # self.load_images(self.app.viewmodel.get_image_list())
        self._image_paths = self._app.capture_vm.get_image_list()
        for idx in list(self._visible_items):
            self._remove_thumbnail(idx)

        # width = max(len(self._image_paths) * self.THUMB_W, 1)
        # self._thumb_canvas.configure(scrollregion=(0, 0, width, 170))
        self._update_thumb_scrollregion()

        # self._update_visible_thumbnails()
        self._thumb_canvas.after_idle(self._update_visible_thumbnails)

        if self._image_paths:
            self._select_image(self._image_paths[-1].file_path)

    def delete_image(self, path):
        # if not messagebox.askyesno("Delete", f"Move\n\n{path.name}\n\nto the Recycle Bin?"):
            # return
        self._app.capture_vm.delete_image(path)

    def _save_browser_window_geometry(self):
        if not self.__browser_window:
            return
        self._browser_window_geometry = self.__browser_window.geometry()
        self._app.settings_vm.image_browser_geometry = self._browser_window_geometry

    def _on_browser_window_configure(self, event=None):
        if not self.__browser_window or not self.__browser_window.winfo_ismapped():
            return
        self._save_browser_window_geometry()

    def _position_browser_window(self):
        if not self.__browser_window or not self._app.root.winfo_ismapped():
            return

        self._app.root.update_idletasks()
        self.__browser_window.update_idletasks()

        if self._browser_window_geometry:
            self.__browser_window.geometry(self._browser_window_geometry)
            return

        x = self._app.root.winfo_rootx() + self._app.root.winfo_width() + 8
        y = self._app.root.winfo_rooty()
        width = 520
        height = min(800, self._app.root.winfo_screenheight() - 40)

        if x + width > self._app.root.winfo_screenwidth():
            x = max(10, self._app.root.winfo_screenwidth() - width - 10)

        if y + height > self._app.root.winfo_screenheight():
            y = max(10, self._app.root.winfo_screenheight() - height - 10)

        self._browser_window_geometry = f"{width}x{height}+{x}+{y}"
        self.__browser_window.geometry(self._browser_window_geometry)

    def _hide_image_browser(self):
        if self.__browser_window:
            self._save_browser_window_geometry()
            self.__browser_window.withdraw()
        self._browser_visible = False

    def _scroll_x(self, *args):
        self._thumb_canvas.xview(*args)
        self._update_visible_thumbnails()

    def _update_thumb_scrollregion(self):
        width = max(len(self._image_paths) * self.THUMB_W, 1)
        self._thumb_canvas.configure(scrollregion=(0, 0, width, 170))

    def _update_visible_thumbnails(self):
        if not self._image_paths:
            return

        self._thumb_canvas.update_idletasks()

        canvas_width = max(1, self._thumb_canvas.winfo_width())

        left = self._thumb_canvas.canvasx(0)
        right = left + canvas_width

        # Only create thumbnails that are actually visible,
        # plus a small preload buffer on either side.
        buffer = 2 * self.THUMB_W

        visible_left = max(0, left - buffer)
        visible_right = right + buffer

        first = max(
            0,
            int(visible_left // self.THUMB_W)
        )

        last = min(
            len(self._image_paths),
            int(visible_right // self.THUMB_W) + 1
        )

        required = set(range(first, last))

        # Remove thumbnails that are far enough outside the viewport.
        for idx in list(self._visible_items):
            if idx not in required:
                self._remove_thumbnail(idx)

        # Create only thumbnails that have entered the viewport/buffer.
        for idx in range(first, last):
            if idx not in self._visible_items:
                self._create_thumbnail(idx)
            else:
                self._update_thumbnail_style(idx)

    def _scroll_to_selected_thumbnail(self):
        if self._selected_index is None or not self._image_paths:
            return

        self._thumb_canvas.update_idletasks()
        canvas_width = max(1, self._thumb_canvas.winfo_width())
        selected_center = (self._selected_index * self.THUMB_W+ self.THUMB_W / 2)

        # Position where the viewport's center should be
        target_left = selected_center - canvas_width / 2

        # Actual scrollable range
        scroll_width = len(self._image_paths) * self.THUMB_W
        max_left = max(0, scroll_width - canvas_width)

        # Don't scroll beyond the valid range
        target_left = max(0, min(target_left, max_left))

        # Convert pixel position to xview fraction
        fraction = target_left / scroll_width

        self._thumb_canvas.xview_moveto(fraction)

        self._update_visible_thumbnails()

    def _remove_thumbnail(self, idx):
        item = self._visible_items.pop(idx, None)

        if not item:
            return

        self._thumb_canvas.delete(item["image"])
        self._thumb_canvas.delete(item["text"])
        self._thumb_canvas.delete(item["delete"])

    def _get_thumbnail_text_style(self, idx):
        if idx == self._selected_index:
            return "#058b9c", ("TkDefaultFont", 12, "bold", "italic")
        return "black", ("TkDefaultFont", 9)

    def _update_thumbnail_style(self, idx):
        item = self._visible_items.get(idx)
        if not item:
            return

        fill, font = self._get_thumbnail_text_style(idx)
        self._thumb_canvas.itemconfigure(item["text"], fill=fill, font=font)

    def _create_thumbnail(self, idx):
        path = self._image_paths[idx].file_path

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
            image_id = self._thumb_canvas.create_image(
                x,
                60,
                image=photo
            )

            fill, font = self._get_thumbnail_text_style(idx)
            text_id = self._thumb_canvas.create_text(
                x,
                140,
                text=path.name,
                width=140,
                fill=fill,
                font=font
            )

            self._thumb_canvas.tag_bind(
                image_id,
                "<Button-1>",
                lambda e, p=path: self._select_image(p)
            )

            delete_id = self._thumb_canvas.create_text(
                x,
                160,
                text="❌ Delete",
                fill="red",
                font=("Segoe UI Emoji", 10, "bold")
            )

            self._thumb_canvas.tag_bind(
                delete_id,
                "<Button-1>",
                lambda e, p=path: self.delete_image(p)
            )

            self._visible_items[idx] = {
                "image": image_id,
                "text": text_id,
                "delete": delete_id,
                "photo": photo
            }
        except Exception as exc:
            self.__logger.error(f"_create_thumb: {exc}")

    def _on_preview_resize(self, event):
        self._update_preview_image()

    def _update_preview_image(self):
        if self._original_image is None:
            return

        w = self._large_thumb_canvas.winfo_width()
        h = self._large_thumb_canvas.winfo_height()

        if w < 10 or h < 10:
            return

        img = self._original_image.copy()
        img.thumbnail( (w - 10, h - 10), Image.Resampling.LANCZOS )
        self._large_thumb_photo = ImageTk.PhotoImage(img)
        self._large_thumb_canvas.delete("all")
        self._image_item = self._large_thumb_canvas.create_image(w // 2,
                                                             h // 2,
                                                             image=self._large_thumb_photo)
        self._large_thumb_canvas.tag_bind(self._image_item,
                                      "<Button-1>",
                                      self._open_external_viewer)

    def _select_image(self, path):
        self._selected_path = path
        try:
            if self._original_image is not None:
                self._original_image.close()
            self._original_image = Image.open(path)
            self._large_thumb_label.configure(text=path.name)
            self._update_preview_image()

        except (OSError, ) as e:
            self.__logger.error(f"{e}")
            self._app.auto_dissapearing_warning("Screenshot not found",
                                               f"Missing file:\n{path}\n\nRefreshing log..."
                                               )
            self._large_thumb_canvas.delete("all")
            self._large_thumb_canvas.create_text(anchor="nw",
                                             text=str(e))
            self._large_thumb_label.configure(text="")
            self._app.auto_dissapearing_warning("Screenshot not found",
                                                           f"Missing file:\n{path}\n\nRefreshing log..."
                                                           )
        else:
            try:
                self._selected_index = get_img_entry_index_by_path(path, self._image_paths)
            except ValueError:
                self._selected_index = None
            self._update_visible_thumbnails()
            self._scroll_to_selected_thumbnail()

    # pylint: disable=unused-argument
    def _open_external_viewer(self, event=None):
        if self._selected_path and self._selected_path.exists():
            os.startfile(self._selected_path)
            return

        self._app.auto_dissapearing_warning("File not found",
                                           f"The image file no longer exists:\n{self._selected_path}",
                                           timeout=4000
                                           )

