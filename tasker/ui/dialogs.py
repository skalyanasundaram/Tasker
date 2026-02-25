import tkinter as tk
from tkinter import filedialog, messagebox

from ..constants import GLOBAL_HOTKEY, CONFIG_FILE, DEFAULT_DATA_FILE
from ..storage import save_config, save_tasks, load_tasks


def open_settings(root, app):
    """Open the settings dialog (Alt+E)."""
    dlg = tk.Toplevel(root)
    dlg.title("Settings")
    dlg.geometry("420x160")
    dlg.transient(root)
    dlg.grab_set()
    dlg.configure(bg="#FFFFFF")

    tk.Label(dlg, text="Tasks JSON file path:", bg="#FFFFFF",
             font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(10, 0))

    path_var = tk.StringVar(value=app.data_file)
    tk.Entry(dlg, textvariable=path_var,
             font=("Segoe UI", 10)).pack(fill=tk.X, padx=10, pady=4)

    def _browse():
        p = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="tasks.json",
        )
        if p:
            path_var.set(p)

    def _apply():
        new_path = path_var.get().strip()
        if not new_path:
            return
        import os
        if not os.path.exists(new_path):
            save_tasks(new_path, app.tasks)
        app.data_file = new_path
        app.cfg["data_file"] = new_path
        save_config(app.cfg)
        app.tasks = load_tasks(app.data_file)
        app._rebuild_rows()
        dlg.destroy()

    btn_frame = tk.Frame(dlg, bg="#FFFFFF")
    btn_frame.pack(fill=tk.X, padx=10, pady=8)
    tk.Button(btn_frame, text="Browse...", command=_browse, width=10).pack(side=tk.LEFT)
    tk.Button(btn_frame, text="Apply", command=_apply, width=10).pack(side=tk.LEFT, padx=6)
    tk.Button(btn_frame, text="Cancel", command=dlg.destroy, width=10).pack(side=tk.RIGHT)

    tk.Label(dlg, text=f"Global Hotkey: Ctrl+K, Ctrl+K  |  Config: {CONFIG_FILE}",
             bg="#FFFFFF", fg="#999999",
             font=("Segoe UI", 8)).pack(side=tk.BOTTOM, pady=4)

    dlg.bind("<Escape>", lambda e: dlg.destroy())


def open_first_run_config(root):
    """First-run dialog asking for the tasks JSON file location.

    Returns the chosen path, or DEFAULT_DATA_FILE if cancelled.
    """
    result = {"path": DEFAULT_DATA_FILE}

    dlg = tk.Toplevel(root)
    dlg.title("Tasker – First Time Setup")
    dlg.geometry("460x200")
    dlg.transient(root)
    dlg.grab_set()
    dlg.configure(bg="#FFFFFF")
    dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # prevent closing

    tk.Label(dlg, text="Welcome to Tasker!", bg="#FFFFFF",
             font=("Segoe UI", 12, "bold")).pack(pady=(16, 4))
    tk.Label(dlg, text="Choose where to store your tasks JSON file.\n"
             "Tip: pick a OneDrive folder to sync across devices.",
             bg="#FFFFFF", font=("Segoe UI", 9),
             justify=tk.CENTER).pack(pady=(0, 8))

    path_var = tk.StringVar(value=DEFAULT_DATA_FILE)
    tk.Entry(dlg, textvariable=path_var,
             font=("Segoe UI", 10)).pack(fill=tk.X, padx=16, pady=4)

    def _browse():
        p = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="tasks.json",
        )
        if p:
            path_var.set(p)

    def _ok():
        result["path"] = path_var.get().strip() or DEFAULT_DATA_FILE
        dlg.destroy()

    dlg.bind("<Escape>", lambda e: _ok())

    btn_frame = tk.Frame(dlg, bg="#FFFFFF")
    btn_frame.pack(fill=tk.X, padx=16, pady=10)
    tk.Button(btn_frame, text="Browse...", command=_browse,
              width=10).pack(side=tk.LEFT)
    tk.Button(btn_frame, text="OK", command=_ok,
              width=10).pack(side=tk.RIGHT)

    root.wait_window(dlg)
    return result["path"]


KEYBINDINGS = [
    ("Up / Down", "Navigate between tasks"),
    ("Tab / Shift+Tab", "Navigate between row components"),
    ("Shift+Up / Shift+Down", "Reorder task with children"),
    ("Shift+Enter", "Insert new task below"),
    ("Shift+Right", "Indent task (make child)"),
    ("Shift+Left", "Un-indent task"),
    ("Ctrl+Space", "Toggle task complete"),
    ("Space / Enter", "Activate focused component"),
    ("Alt+S", "Cycle star color"),
    ("Alt+R", "Open reminder picker"),
    ("Ctrl+D", "Delete task"),
    ("Escape", "Hide to system tray"),
    ("Ctrl+K, Ctrl+K", "Global show/hide"),
    ("Alt+C", "Switch active / completed view"),
    ("Alt+E", "Open settings"),
    ("Alt+K", "Show keybindings"),
]


def open_keybindings(root):
    """Show the keybindings reference dialog."""
    dlg = tk.Toplevel(root)
    dlg.title("Keybindings")
    dlg.geometry("380x400")
    dlg.transient(root)
    dlg.grab_set()
    dlg.configure(bg="#FFFFFF")

    tk.Label(dlg, text="Keyboard Shortcuts", bg="#FFFFFF",
             font=("Segoe UI", 11, "bold")).pack(pady=(12, 8))

    frame = tk.Frame(dlg, bg="#FFFFFF")
    frame.pack(fill=tk.BOTH, expand=True, padx=16)

    for shortcut, description in KEYBINDINGS:
        row = tk.Frame(frame, bg="#FFFFFF")
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=shortcut, bg="#FFFFFF", fg="#2266AA",
                 font=("Consolas", 9), width=22,
                 anchor="w").pack(side=tk.LEFT)
        tk.Label(row, text=description, bg="#FFFFFF", fg="#444444",
                 font=("Segoe UI", 9),
                 anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(dlg, text="Close", command=dlg.destroy,
              width=10).pack(pady=12)
    dlg.bind("<Escape>", lambda e: dlg.destroy())
