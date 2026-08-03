import tkinter as tk


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