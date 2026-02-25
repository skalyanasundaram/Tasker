import tkinter as tk

from ..constants import TITLE_HEIGHT


class TitleBar(tk.Frame):
    """Custom thin title bar with drag support, minimize and close buttons."""

    def __init__(self, parent, *, on_close, on_minimize, on_toggle_view):
        super().__init__(parent, bg="#444444", height=TITLE_HEIGHT)
        self.pack(fill=tk.X, side=tk.TOP)
        self.pack_propagate(False)

        self._root = parent
        self._drag_data = {"x": 0, "y": 0}
        self._on_toggle_view = on_toggle_view
        self._showing_completed = False

        # title text
        label = tk.Label(self, text=" Tasker", fg="#CCCCCC", bg="#444444",
                         font=("Segoe UI", 9))
        label.pack(side=tk.LEFT, padx=4)

        # close button
        close_btn = tk.Label(self, text=" ✕ ", fg="#CCCCCC", bg="#444444",
                             font=("Segoe UI", 9), cursor="hand2")
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: on_close())

        # minimize button
        min_btn = tk.Label(self, text=" — ", fg="#CCCCCC", bg="#444444",
                           font=("Segoe UI", 9), cursor="hand2")
        min_btn.pack(side=tk.RIGHT)
        min_btn.bind("<Button-1>", lambda e: on_minimize())

        # view toggle label (shows current view mode)
        self._view_label = tk.Label(self, text="Active ▾", fg="#88BBFF",
                                    bg="#444444", font=("Segoe UI", 8),
                                    cursor="hand2")
        self._view_label.pack(side=tk.RIGHT, padx=6)
        self._view_label.bind("<Button-1>", self._toggle_view)

        # drag support
        for w in (self, label):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

    def _toggle_view(self, _event=None):
        self._showing_completed = not self._showing_completed
        if self._showing_completed:
            self._view_label.config(text="Completed ▾")
        else:
            self._view_label.config(text="Active ▾")
        self._on_toggle_view(self._showing_completed)

    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root - self._root.winfo_x()
        self._drag_data["y"] = event.y_root - self._root.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self._root.geometry(f"+{x}+{y}")
