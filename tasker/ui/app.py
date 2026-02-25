import tkinter as tk
from tkinter import messagebox
import datetime
import time as _time
import os
import sys

try:
    import keyboard as _kb
    HAS_HOTKEY = True
except ImportError:
    HAS_HOTKEY = False

from ..constants import (
    STAR_COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, GLOBAL_HOTKEY,
    DEFAULT_DATA_FILE, REMINDER_CHECK_MS,
)
from ..storage import load_config, load_tasks, save_tasks, save_config
from ..tray import create_tray_icon
from .title_bar import TitleBar
from .task_list import TaskList
from .dialogs import open_settings, open_first_run_config, open_keybindings


class TaskerApp:
    """Main application window and controller."""

    def __init__(self):
        self.selected_index = None
        self.tray_icon = None
        self.running = True
        self.show_completed = False

        # ---- root window (frameless) ----
        self.root = tk.Tk()
        self.root.title("Tasker")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#333333")

        # position bottom-right
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - WINDOW_WIDTH - 16
        y = sh - WINDOW_HEIGHT - 60
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.root.minsize(300, 200)
        self.root.resizable(True, True)

        # ---- first-run config ----
        self.cfg = load_config()
        if self.cfg is None:
            # first run – ask user where to store tasks
            chosen_path = open_first_run_config(self.root)
            self.cfg = {"data_file": chosen_path}
            save_config(self.cfg)

        self.data_file = self.cfg.get("data_file", DEFAULT_DATA_FILE)
        self.tasks = load_tasks(self.data_file)
        self._file_mtime = self._get_file_mtime()
        self._last_save_ts = 0.0

        # ---- title bar ----
        self.title_bar = TitleBar(self.root, on_close=self.quit_app,
                                  on_minimize=self.hide_window,
                                  on_toggle_view=self._set_view)

        # ---- task list ----
        callbacks = {
            "on_focus": self._select_row,
            "on_text_change": self._update_text,
            "on_done_toggle": self._toggle_done,
            "on_star_toggle": self._toggle_star,
            "on_shift_enter": self._insert_row_below,
            "on_reminder_click": self._open_inline_reminder,
            # keyboard navigation
            "on_up": self._nav_up,
            "on_down": self._nav_down,
            "on_indent": self._indent_row,
            "on_unindent": self._unindent_row,
            "on_toggle_done_kb": self._toggle_done_kb,
            "on_toggle_star_kb": self._toggle_star_kb,
            "on_delete": self._delete_row,
            "on_move_up": self._move_row_up,
            "on_move_down": self._move_row_down,
        }
        self.task_list = TaskList(self.root, task_callbacks=callbacks)
        self._rebuild_rows()

        # ---- resize grip ----
        self._resize_data = {}
        grip = tk.Label(self.root, text="⋱", fg="#888888", bg="#333333",
                        cursor="size_nw_se", font=("Segoe UI", 8))
        grip.place(relx=1.0, rely=1.0, anchor="se")
        grip.bind("<Button-1>", self._start_resize)
        grip.bind("<B1-Motion>", self._on_resize)

        # ---- key bindings ----
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<Alt-e>", lambda e: open_settings(self.root, self))
        self.root.bind("<Alt-k>", lambda e: open_keybindings(self.root))
        self.root.bind("<Alt-c>", lambda e: self._toggle_view())

        # ---- system tray ----
        self.tray_icon = create_tray_icon(
            on_show=lambda: self.root.after(0, self.show_window),
            on_quit=lambda: self.root.after(0, self.quit_app),
        )

        # ---- global hotkey: Ctrl+K, Ctrl+K chord ----
        self._hotkey_state = 0  # 0 = idle, 1 = first Ctrl+K pressed
        self._hotkey_ts = 0.0
        self._kb_hook = None
        if HAS_HOTKEY:
            try:
                self._kb_hook = _kb.on_press(self._on_key_press)
                print("[Tasker] Global hotkey registered (Ctrl+K, Ctrl+K)",
                      file=sys.stderr)
            except Exception as e:
                print(f"[Tasker] Failed to register global hotkey: {e}",
                      file=sys.stderr)

        # ---- reminder checker ----
        self._check_reminders()

        # ---- file watcher (reload on external edits) ----
        self._watch_file()

    # ---- Ctrl+K, Ctrl+K chord ----
    def _on_key_press(self, event):
        """Detect Ctrl+K, Ctrl+K chord via keyboard.on_press."""
        try:
            key_name = event.name.lower() if event.name else ""
            # Check for Ctrl+K
            is_ctrl_k = (key_name == "k" and
                         any(mod in event.modifiers or []
                             for mod in ("ctrl", "left ctrl", "right ctrl"))
                         if hasattr(event, "modifiers") and event.modifiers
                         else key_name == "k" and _kb.is_pressed("ctrl"))

            if is_ctrl_k:
                now = _time.time()
                if self._hotkey_state == 1 and (now - self._hotkey_ts) < 1.0:
                    self._hotkey_state = 0
                    self._toggle_visibility()
                else:
                    self._hotkey_state = 1
                    self._hotkey_ts = now
            elif key_name not in ("ctrl", "left ctrl", "right ctrl",
                                  "control_l", "control_r", ""):
                # any non-ctrl, non-k key resets the chord
                self._hotkey_state = 0
        except Exception:
            pass

    # ---- view toggle (active / completed) ----
    def _set_view(self, show_completed):
        self.show_completed = show_completed
        self._rebuild_rows()

    def _toggle_view(self):
        """Toggle between active and completed view (Alt+C)."""
        self.title_bar._toggle_view()

    # ---- resize helpers ----
    def _start_resize(self, event):
        self._resize_data = {
            "x": event.x_root, "y": event.y_root,
            "w": self.root.winfo_width(), "h": self.root.winfo_height(),
        }

    def _on_resize(self, event):
        dw = event.x_root - self._resize_data["x"]
        dh = event.y_root - self._resize_data["y"]
        new_w = max(300, self._resize_data["w"] + dw)
        new_h = max(200, self._resize_data["h"] + dh)
        self.root.geometry(f"{new_w}x{new_h}")

    # ---- row actions (callbacks from TaskRow) ----
    def _select_row(self, index):
        self.selected_index = index
        self.task_list.update_selection(index)

    def _update_text(self, index, var):
        if index < len(self.tasks) and not self.tasks[index].get("done", False):
            self.tasks[index]["text"] = var.get()
            self._save()

    def _toggle_done(self, index, var):
        self.tasks[index]["done"] = var.get()
        # cascade to children: completing or un-completing a parent
        # also completes or un-completes all its children
        parent_indent = self.tasks[index].get("indent", 0)
        for j in range(index + 1, len(self.tasks)):
            if self.tasks[j].get("indent", 0) > parent_indent:
                self.tasks[j]["done"] = var.get()
            else:
                break
        self._save_and_rebuild()

    def _toggle_star(self, index):
        cur = self.tasks[index].get("star", 0)
        self.tasks[index]["star"] = (cur + 1) % len(STAR_COLORS)
        self._save_and_rebuild()

    def _insert_row_below(self, index):
        new_task = {
            "text": "", "done": False, "star": 0,
            "indent": self.tasks[index].get("indent", 0), "reminder": None,
        }
        self.tasks.insert(index + 1, new_task)
        self.selected_index = index + 1
        self._save_and_rebuild()
        self.task_list.focus_row(self.selected_index)
        return "break"

    def _indent_row(self, index):
        if index > 0:
            cur = self.tasks[index].get("indent", 0)
            prev_indent = self.tasks[index - 1].get("indent", 0)
            if cur <= prev_indent:
                self.tasks[index]["indent"] = cur + 1
                self._save_and_rebuild()
        return "break"

    def _unindent_row(self, index):
        cur = self.tasks[index].get("indent", 0)
        if cur > 0:
            self.tasks[index]["indent"] = cur - 1
            self._save_and_rebuild()
        return "break"

    # ---- keyboard navigation ----
    def _nav_up(self, index):
        """Move focus to the previous row."""
        imap = self.task_list.index_map
        # find display position of current real index
        display_pos = None
        for di, ri in enumerate(imap):
            if ri == index:
                display_pos = di
                break
        if display_pos is not None and display_pos > 0:
            prev_real = imap[display_pos - 1]
            self._select_row(prev_real)
            self.task_list.focus_row(prev_real)
        return "break"

    def _nav_down(self, index):
        """Move focus to the next row (or empty row)."""
        from .task_row import EmptyRow
        imap = self.task_list.index_map
        display_pos = None
        for di, ri in enumerate(imap):
            if ri == index:
                display_pos = di
                break
        if display_pos is not None:
            if display_pos < len(imap) - 1:
                next_real = imap[display_pos + 1]
                self._select_row(next_real)
                self.task_list.focus_row(next_real)
            elif not self.show_completed:
                # focus the empty row at the bottom
                rows = self.task_list.rows
                if rows and isinstance(rows[-1], EmptyRow):
                    rows[-1].entry.focus_set()
        return "break"

    def _toggle_done_kb(self, index):
        """Toggle done via Ctrl+Space."""
        if index < len(self.tasks):
            new_state = not self.tasks[index].get("done", False)
            self.tasks[index]["done"] = new_state
            parent_indent = self.tasks[index].get("indent", 0)
            for j in range(index + 1, len(self.tasks)):
                if self.tasks[j].get("indent", 0) > parent_indent:
                    self.tasks[j]["done"] = new_state
                else:
                    break
            self._save_and_rebuild()
        return "break"

    def _toggle_star_kb(self, index):
        """Toggle star via Alt+S."""
        if index < len(self.tasks):
            self._toggle_star(index)
        return "break"

    def _delete_row(self, index):
        """Delete a task row via Ctrl+D."""
        if index < len(self.tasks):
            self.tasks.pop(index)
            if self.selected_index is not None:
                if self.selected_index >= len(self.tasks):
                    self.selected_index = max(0, len(self.tasks) - 1) if self.tasks else None
            self._save_and_rebuild()
            if self.selected_index is not None:
                self.task_list.focus_row(self.selected_index)
        return "break"

    def _get_task_group(self, index):
        """Return (start, end) slice of a task and all its children."""
        if index >= len(self.tasks):
            return index, index + 1
        parent_indent = self.tasks[index].get("indent", 0)
        end = index + 1
        while end < len(self.tasks):
            if self.tasks[end].get("indent", 0) > parent_indent:
                end += 1
            else:
                break
        return index, end

    def _move_row_up(self, index):
        """Move task + children up via Shift+Up (active view only)."""
        if self.show_completed:
            return "break"
        start, end = self._get_task_group(index)
        if start <= 0:
            return "break"
        # the item just above the group
        above = start - 1
        group = self.tasks[start:end]
        del self.tasks[start:end]
        self.tasks[above:above] = group
        self.selected_index = above
        self._save_and_rebuild()
        self.task_list.focus_row(self.selected_index)
        return "break"

    def _move_row_down(self, index):
        """Move task + children down via Shift+Down (active view only)."""
        if self.show_completed:
            return "break"
        start, end = self._get_task_group(index)
        if end >= len(self.tasks):
            return "break"
        # the item (or group) just below: find its extent
        below_start = end
        below_end = self._get_task_group(below_start)[1]
        group = self.tasks[start:end]
        below_group = self.tasks[below_start:below_end]
        # swap: put below_group first, then group
        self.tasks[start:below_end] = below_group + group
        self.selected_index = start + len(below_group)
        self._save_and_rebuild()
        self.task_list.focus_row(self.selected_index)
        return "break"

    def _commit_empty_row(self, widget):
        text = widget.get().strip()
        if text:
            self.tasks.append({
                "text": text, "done": False, "star": 0,
                "indent": 0, "reminder": None,
            })
            self._save_and_rebuild()

    # ---- inline reminder picker ----
    def _open_inline_reminder(self, index):
        # find the display row index for this real task index
        display_idx = None
        for di, ri in enumerate(self.task_list.index_map):
            if ri == index:
                display_idx = di
                break
        if display_idx is None:
            return

        def _on_set(iso_str):
            self.tasks[index]["reminder"] = iso_str
            self._save_and_rebuild()

        def _on_clear():
            self.tasks[index]["reminder"] = None
            self._save_and_rebuild()

        self.task_list.show_picker(display_idx, self.tasks[index],
                                   _on_set, _on_clear)

    # ---- rebuild / save ----
    def _rebuild_rows(self):
        self.task_list.rebuild(self.tasks, self.selected_index,
                               self._commit_empty_row,
                               show_completed=self.show_completed)

    def _save(self):
        save_tasks(self.data_file, self.tasks)
        self._file_mtime = self._get_file_mtime()
        self._last_save_ts = _time.time()

    def _save_and_rebuild(self):
        self._save()
        self._rebuild_rows()

    # ---- file watcher ----
    def _get_file_mtime(self):
        """Return the modification time of the data file, or 0."""
        try:
            return os.path.getmtime(self.data_file)
        except OSError:
            return 0

    def _watch_file(self):
        """Poll the data file every 60 seconds for external changes."""
        if not self.running:
            return
        try:
            # skip if we saved recently (debounce 5s)
            if (_time.time() - self._last_save_ts) < 5:
                pass
            else:
                current_mtime = self._get_file_mtime()
                if current_mtime and current_mtime != self._file_mtime:
                    self._file_mtime = current_mtime
                    self.tasks = load_tasks(self.data_file)
                    self._rebuild_rows()
        except Exception:
            pass
        self.root.after(60000, self._watch_file)

    # ---- visibility ----
    def _on_escape(self, event):
        """Layered Esc: dismiss picker → switch to active view → hide."""
        # 1. if inline picker is open, dismiss it
        if self.task_list._picker_frame:
            self.task_list.dismiss_picker()
            return "break"
        # 2. if showing completed view, switch to active
        if self.show_completed:
            self._toggle_view()
            return "break"
        # 3. hide the window
        self.hide_window()
        return "break"

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()

    def _toggle_visibility(self):
        self.root.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.root.state() == "withdrawn":
            self.show_window()
        else:
            self.hide_window()

    # ---- reminders ----
    def _check_reminders(self):
        if not self.running:
            return
        now = datetime.datetime.now()
        for i, task in enumerate(self.tasks):
            r = task.get("reminder")
            if r and not task.get("done", False):
                try:
                    dt = datetime.datetime.fromisoformat(r)
                    if dt <= now:
                        task["reminder"] = None
                        self._save()
                        self.show_window()
                        # switch to active view if in completed view
                        if self.show_completed:
                            self.show_completed = False
                        self.selected_index = i
                        self._rebuild_rows()
                        self.root.after(200, lambda i=i: self._flash_reminder(i))
                        break
                except Exception:
                    pass
        self.root.after(REMINDER_CHECK_MS, self._check_reminders)

    def _flash_reminder(self, index):
        self.task_list.flash_row(index)
        if index < len(self.tasks):
            messagebox.showinfo("Reminder",
                                f"Task: {self.tasks[index].get('text', '')}")

    # ---- quit ----
    def quit_app(self):
        self.running = False
        self._save()
        if HAS_HOTKEY:
            try:
                _kb.unhook_all()
            except Exception:
                pass
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()
