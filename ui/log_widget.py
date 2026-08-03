# pylint: disable=missing-docstring,line-too-long

from __future__ import annotations

from pathlib import Path
from subprocess import TimeoutExpired
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from core.logger import get_logger
from core.observer import IObserver
from models.image_entry import ImageEntry

logger = get_logger(__name__)

class ScreenshotLogWidget(IObserver):
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

        self.refresh_picture_logs()

    def update(self,event: str, data=None):
        pass

    def add_entry(self, path_str: str):
        """Add an entry with an open button and selectable text"""
        path = Path(path_str)

        # Main entry container with card-like design
        entry_frame = tk.Frame(self.scrollable_frame, bg="white", relief="flat", bd=0)
        entry_frame.pack(fill="x", padx=8, pady=4)

        # Add border/shadow effect using inner frame
        inner_frame = tk.Frame(entry_frame, bg="white")
        inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # pylint: disable=unused-argument
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

        btn = tk.Button(btn_frame, text="📁", command=lambda: self._cmd_open_path(path),
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

    def remove_entry(self, path):
        logger.info(f"remove_entry {path}")
        for (entry_f, p) in self.entries:
            if p == path:
                entry_f.destroy()
        # self._update_scroll_region()

    def clear(self):
        """Clear all entries from the log"""
        for entry_frame, _ in self.entries:
            entry_frame.destroy()
        self.entries.clear()

    def refresh_picture_logs(self):
        """Refresh log by reading all PNG files from the repository"""
        self.clear()
        pics_list:list[ImageEntry] = self.app.viewmodel.image_repository.get_list()
        try:
            if pics_list:
                for img_entry in pics_list:
                    self.add_entry(img_entry.file_path)
                # Update scroll region after all entries are added
                self._update_scroll_region()
                # messagebox.showinfo("Refresh complete", f"Found {len(self.app.pics_list)} PNG file(s).")
        except (FileNotFoundError, FileExistsError, FloatingPointError)  as e:
            logger.error(f"refresh_picture_logs: {e}")
            messagebox.showerror("Error", f"Failed to refresh: {e}")

    def refresh_first_image_index(self, data):
        old_img_path, new_img_path = data
        for (entry_f, p) in self.entries:
            if p == old_img_path:
                inner_frame = entry_f.winfo_children()[0]
                btn_frame = inner_frame.winfo_children()[0]
                btn = btn_frame.winfo_children()[0]  # ← Get the Button from inside btn_frame
                text_frame = inner_frame.winfo_children()[1]
                text_widget = text_frame.winfo_children()[0]

                text_widget.config(state=tk.NORMAL)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", new_img_path)
                text_widget.config(state=tk.DISABLED)
                text_widget.update()  # Force update to reflect changes
                self.app.root.update_idletasks()  # Update the main window to reflect changes

                btn.config(command=lambda: self._cmd_open_path(new_img_path))
                return


    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

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
        self.parent.update()

        # Scroll to bottom using a more forceful method
        self.canvas.yview_scroll(999999, "units")

    def _cmd_open_path(self, new_img_path: Path):
        if new_img_path.exists():
            import subprocess
            try:
                # Open file explorer and select the file
                subprocess.Popen(f'explorer /select,"{new_img_path}"')
            except (OSError, ValueError, TimeoutExpired ) as e:
                messagebox.showerror(e)
        else:
            messagebox.showwarning("Path not found", f"The path does not exist:\n{new_img_path}\n\nRefreshing log...")
            self.refresh_picture_logs()