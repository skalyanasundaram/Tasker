import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

from ..constants import GLOBAL_HOTKEY, CONFIG_FILE, DEFAULT_DATA_FILE
from ..storage import save_config, save_tasks, load_tasks


def open_settings(root, app):
    """Open the settings dialog (Alt+E)."""
    dlg = tk.Toplevel(root)
    dlg.title("Settings")
    dlg.geometry("520x260")
    dlg.transient(root)
    dlg.grab_set()
    dlg.configure(bg="#FFFFFF")

    notebook = ttk.Notebook(dlg)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    storage_tab = tk.Frame(notebook, bg="#FFFFFF")
    ms_tab = tk.Frame(notebook, bg="#FFFFFF")
    notebook.add(storage_tab, text="Storage")
    notebook.add(ms_tab, text="Microsoft To Do")

    # ---- Storage tab ----
    tk.Label(storage_tab, text="Tasks JSON file path:", bg="#FFFFFF",
             font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(10, 0))

    path_var = tk.StringVar(value=app.data_file)
    tk.Entry(storage_tab, textvariable=path_var,
             font=("Segoe UI", 10)).pack(fill=tk.X, padx=10, pady=4)

    def _browse():
        p = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="tasks.json",
        )
        if p:
            path_var.set(p)

    tk.Button(storage_tab, text="Browse...", command=_browse,
              width=10).pack(anchor="w", padx=10, pady=(0, 8))

    # ---- Microsoft To Do tab ----
    ms_enabled_var = tk.BooleanVar(value=app.ms_sync_enabled)
    tk.Checkbutton(
        ms_tab,
        text="Enable Microsoft To Do sync (one-way push)",
        variable=ms_enabled_var,
        bg="#FFFFFF",
    ).pack(anchor="w", padx=10, pady=(10, 4))

    tk.Label(ms_tab, text="Task List Name:", bg="#FFFFFF",
             font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 0))
    list_name_var = tk.StringVar(value=app.ms_tasklist_name or "Tasker")
    tk.Entry(ms_tab, textvariable=list_name_var,
             font=("Segoe UI", 10)).pack(fill=tk.X, padx=10, pady=4)

    tk.Label(ms_tab, text="Client ID (Azure App Registration):", bg="#FFFFFF",
             font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(6, 0))
    client_id_var = tk.StringVar(value=app.ms_client_id or "")
    tk.Entry(ms_tab, textvariable=client_id_var,
             font=("Segoe UI", 10)).pack(fill=tk.X, padx=10, pady=4)

    tk.Label(
        ms_tab,
        text="First sync will open a browser for consent and store a token in "
             "~/.tasker/ms_token_cache.json",
        bg="#FFFFFF",
        fg="#666666",
        font=("Segoe UI", 8),
        wraplength=460,
        justify=tk.LEFT,
    ).pack(anchor="w", padx=10, pady=(6, 0))

    def _test_sync():
        client_id = client_id_var.get().strip()
        if not client_id:
            messagebox.showerror("Missing Client ID",
                                 "Enter your Azure App Client ID first.")
            return
        list_name = list_name_var.get().strip() or "Tasker"
        progress = tk.Toplevel(dlg)
        progress.title("Syncing...")
        progress.geometry("280x100")
        progress.transient(dlg)
        progress.grab_set()
        progress.configure(bg="#FFFFFF")
        tk.Label(progress, text="Syncing to Microsoft To Do...",
                 bg="#FFFFFF", font=("Segoe UI", 9)).pack(pady=18)
        progress.update_idletasks()

        def _run():
            error = None
            new_account_id = None
            try:
                from ..ms_todo_sync import push_tasks
                new_account_id = push_tasks(
                    list(app.tasks),
                    list_name,
                    client_id,
                    account_id=app.ms_account_id or None,
                    interactive=True,
                )
            except Exception as exc:
                error = exc

            def _done():
                progress.destroy()
                if new_account_id:
                    app.ms_account_id = new_account_id
                    app.cfg["ms_account_id"] = new_account_id
                    app.ms_client_id = client_id
                    app.ms_tasklist_name = list_name
                    app.cfg["ms_client_id"] = client_id
                    app.cfg["ms_tasklist_name"] = list_name
                    save_config(app.cfg)
                if error:
                    messagebox.showerror("Sync Failed", str(error))
                else:
                    messagebox.showinfo("Sync Success",
                                        "Microsoft To Do sync completed.")

            dlg.after(0, _done)

        threading.Thread(target=_run, daemon=True).start()

    tk.Button(ms_tab, text="Test Sync", command=_test_sync,
              width=12).pack(anchor="w", padx=10, pady=(8, 0))

    def _persist_settings():
        new_path = path_var.get().strip()
        if new_path:
            import os
            if not os.path.exists(new_path):
                save_tasks(new_path, app.tasks)
            app.data_file = new_path
            app.cfg["data_file"] = new_path
        else:
            app.cfg["data_file"] = app.data_file
        app.ms_sync_enabled = bool(ms_enabled_var.get())
        app.ms_tasklist_name = list_name_var.get().strip() or "Tasker"
        app.ms_client_id = client_id_var.get().strip()
        app.cfg["ms_sync_enabled"] = app.ms_sync_enabled
        app.cfg["ms_tasklist_name"] = app.ms_tasklist_name
        app.cfg["ms_client_id"] = app.ms_client_id
        save_config(app.cfg)
        app.tasks = load_tasks(app.data_file)
        app._rebuild_rows()
        if app.ms_sync_enabled:
            app._schedule_ms_sync(delay_ms=0)
        else:
            if app._ms_sync_timer is not None:
                try:
                    app.root.after_cancel(app._ms_sync_timer)
                except Exception:
                    pass
                app._ms_sync_timer = None

    def _close():
        _persist_settings()
        dlg.destroy()

    btn_frame = tk.Frame(dlg, bg="#FFFFFF")
    btn_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
    tk.Button(btn_frame, text="Close", command=_close,
              width=10).pack(side=tk.RIGHT)

    tk.Label(dlg, text=f"Global Hotkey: Ctrl+K, Ctrl+K  |  Config: {CONFIG_FILE}",
             bg="#FFFFFF", fg="#999999",
             font=("Segoe UI", 8)).pack(side=tk.BOTTOM, pady=4)

    dlg.bind("<Escape>", lambda e: _close())
    dlg.protocol("WM_DELETE_WINDOW", _close)


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
