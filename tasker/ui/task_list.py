import tkinter as tk
from tkinter import ttk

from ..constants import SELECTED_ROW_BG, DEFAULT_ROW_BG, REMINDER_FLASH_BG
from .task_row import TaskRow, EmptyRow


class TaskList:
    """Scrollable list of task rows backed by a Canvas."""

    def __init__(self, parent, *, task_callbacks):
        self._task_callbacks = task_callbacks
        self.rows: list[TaskRow | EmptyRow] = []
        # maps display index -> actual task list index
        self.index_map: list[int] = []

        container = tk.Frame(parent, bg="#333333")
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))

        self.canvas = tk.Canvas(container, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL,
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.canvas, bg="#FFFFFF")
        self._cw = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_frame_cfg)
        self.canvas.bind("<Configure>", self._on_canvas_cfg)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # inline date picker frame (hidden by default)
        self._picker_frame = None

    # ----- scroll plumbing -----
    def _on_frame_cfg(self, _e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_cfg(self, e):
        self.canvas.itemconfig(self._cw, width=e.width)

    def _on_mousewheel(self, e):
        self.canvas.yview_scroll(-1 * (e.delta // 120), "units")

    # ----- rebuild -----
    def rebuild(self, tasks, selected_index, on_empty_commit,
                show_completed=False):
        self.dismiss_picker()
        for r in self.rows:
            r.frame.destroy()
        self.rows.clear()
        self.index_map.clear()

        for real_i, task in enumerate(tasks):
            is_done = task.get("done", False)
            # filter: show only completed or only active
            if show_completed and not is_done:
                continue
            if not show_completed and is_done:
                continue

            display_i = len(self.index_map)
            self.index_map.append(real_i)
            row = TaskRow(self.inner, real_i, task,
                          selected=(real_i == selected_index),
                          callbacks=self._task_callbacks,
                          readonly=show_completed)
            self.rows.append(row)

        # only show empty row in active view
        if not show_completed:
            def _on_empty_up():
                # move focus to last task row
                if self.index_map:
                    self.rows[-2].entry.focus_set()  # -2 because -1 is EmptyRow
            empty = EmptyRow(self.inner, on_empty_commit, on_up=_on_empty_up)
            self.rows.append(empty)

    # ----- selection highlight -----
    def update_selection(self, selected_index):
        for i, r in enumerate(self.rows):
            if isinstance(r, TaskRow):
                real_i = self.index_map[i] if i < len(self.index_map) else -1
                bg = SELECTED_ROW_BG if real_i == selected_index else DEFAULT_ROW_BG
                r.set_bg(bg)

    def flash_row(self, real_index):
        for i, r in enumerate(self.rows):
            if isinstance(r, TaskRow) and i < len(self.index_map):
                if self.index_map[i] == real_index:
                    r.set_bg(REMINDER_FLASH_BG)
                    r.entry.focus_set()
                    break

    def focus_row(self, real_index):
        for i, r in enumerate(self.rows):
            if isinstance(r, TaskRow) and i < len(self.index_map):
                if self.index_map[i] == real_index:
                    r.entry.focus_set()
                    break

    # ----- inline date/time picker -----
    def show_picker(self, row_index, task, on_set, on_clear):
        """Show an inline date/time picker below the given row."""
        self.dismiss_picker()

        # find the row widget and pack picker after it
        if row_index >= len(self.rows):
            return
        row_widget = self.rows[row_index]

        import datetime
        self._picker_frame = tk.Frame(self.inner, bg="#F8F8E8", bd=1,
                                      relief=tk.SOLID)

        # position it right after the target row
        self._picker_frame.pack(fill=tk.X, padx=0, pady=0,
                                after=row_widget.frame)

        now = datetime.datetime.now()
        existing = task.get("reminder")
        if existing:
            try:
                dt = datetime.datetime.fromisoformat(existing)
            except Exception:
                dt = now
        else:
            dt = now + datetime.timedelta(hours=1)

        pf = self._picker_frame

        # date row
        date_row = tk.Frame(pf, bg="#F8F8E8")
        date_row.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(date_row, text="Date:", bg="#F8F8E8",
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)

        year_var = tk.IntVar(value=dt.year)
        year_spin = tk.Spinbox(date_row, from_=2024, to=2035,
                               textvariable=year_var, width=5,
                               font=("Segoe UI", 9))
        year_spin.pack(side=tk.LEFT, padx=2)

        tk.Label(date_row, text="/", bg="#F8F8E8").pack(side=tk.LEFT)

        month_var = tk.IntVar(value=dt.month)
        month_spin = tk.Spinbox(date_row, from_=1, to=12,
                                textvariable=month_var, width=3,
                                font=("Segoe UI", 9), format="%02.0f")
        month_spin.pack(side=tk.LEFT, padx=2)

        tk.Label(date_row, text="/", bg="#F8F8E8").pack(side=tk.LEFT)

        day_var = tk.IntVar(value=dt.day)
        day_spin = tk.Spinbox(date_row, from_=1, to=31,
                              textvariable=day_var, width=3,
                              font=("Segoe UI", 9), format="%02.0f")
        day_spin.pack(side=tk.LEFT, padx=2)

        # time row
        time_row = tk.Frame(pf, bg="#F8F8E8")
        time_row.pack(fill=tk.X, padx=8, pady=2)

        tk.Label(time_row, text="Time:", bg="#F8F8E8",
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)

        hour_var = tk.IntVar(value=dt.hour)
        hour_spin = tk.Spinbox(time_row, from_=0, to=23,
                               textvariable=hour_var, width=3,
                               font=("Segoe UI", 9), format="%02.0f")
        hour_spin.pack(side=tk.LEFT, padx=2)

        tk.Label(time_row, text=":", bg="#F8F8E8").pack(side=tk.LEFT)

        min_var = tk.IntVar(value=dt.minute)
        min_spin = tk.Spinbox(time_row, from_=0, to=59,
                              textvariable=min_var, width=3,
                              font=("Segoe UI", 9), format="%02.0f")
        min_spin.pack(side=tk.LEFT, padx=2)

        # buttons row
        btn_row = tk.Frame(pf, bg="#F8F8E8")
        btn_row.pack(fill=tk.X, padx=8, pady=(2, 6))

        def _do_set():
            try:
                new_dt = datetime.datetime(
                    year_var.get(), month_var.get(), day_var.get(),
                    hour_var.get(), min_var.get(),
                )
                on_set(new_dt.isoformat())
            except ValueError:
                pass  # invalid date combo
            self.dismiss_picker()

        def _do_clear():
            on_clear()
            self.dismiss_picker()

        tk.Button(btn_row, text="Set", command=_do_set,
                  width=6, font=("Segoe UI", 8)).pack(side=tk.LEFT)
        tk.Button(btn_row, text="Clear", command=_do_clear,
                  width=6, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_row, text="Cancel", command=self.dismiss_picker,
                  width=6, font=("Segoe UI", 8)).pack(side=tk.RIGHT)

        # Esc dismisses the picker from any spinbox/button inside it
        for w in (year_spin, month_spin, day_spin, hour_spin, min_spin, pf):
            w.bind("<Escape>", lambda e: self.dismiss_picker())

    def dismiss_picker(self):
        if self._picker_frame:
            self._picker_frame.destroy()
            self._picker_frame = None
