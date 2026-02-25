import tkinter as tk
import datetime

from ..constants import (
    STAR_COLORS, SELECTED_ROW_BG, DEFAULT_ROW_BG, COMPLETED_FG,
    COMPLETED_ROW_BG, FOCUS_BORDER_COLOR, UNFOCUS_BORDER_COLOR,
)

# Focus ring style for labels (star, reminder)
_FOCUS_PAD = 1
_FOCUS_RELIEF = tk.SOLID


def _add_focus_ring(widget):
    """Add visible focus/unfocus ring to a label widget."""
    widget.config(borderwidth=_FOCUS_PAD, relief=tk.FLAT)
    widget.bind("<FocusIn>", lambda e: widget.config(
        relief=_FOCUS_RELIEF, highlightbackground=FOCUS_BORDER_COLOR), add="+")
    widget.bind("<FocusOut>", lambda e: widget.config(
        relief=tk.FLAT), add="+")


class TaskRow:
    """A single task row rendered inside a parent frame."""

    def __init__(self, parent, index, task, *, selected, callbacks,
                 readonly=False):
        bg = SELECTED_ROW_BG if selected else (
            COMPLETED_ROW_BG if readonly else DEFAULT_ROW_BG
        )

        self.frame = tk.Frame(parent, bg=bg, bd=0,
                              highlightthickness=1, highlightbackground=UNFOCUS_BORDER_COLOR)
        self.frame.pack(fill=tk.X, padx=0, pady=0)

        indent = int(task.get("indent", 0) or 0)
        self._callbacks = callbacks
        self._index = index
        self._readonly = readonly
        self._bg = bg

        # col 1: checkbox (always enabled so completed tasks can be unmarked)
        self.done_var = tk.BooleanVar(value=task.get("done", False))
        self.chk = tk.Checkbutton(
            self.frame, variable=self.done_var, bg=bg, activebackground=bg,
            command=lambda: callbacks["on_done_toggle"](index, self.done_var),
            takefocus=1, highlightthickness=2,
            highlightcolor=FOCUS_BORDER_COLOR,
            highlightbackground=bg,
        )
        self.chk.pack(side=tk.LEFT, padx=(4 + indent * 20, 0))

        # col 2: task text
        self.text_var = tk.StringVar(value=task.get("text", ""))
        self.entry = tk.Entry(
            self.frame, textvariable=self.text_var, relief=tk.FLAT, bg=bg,
            font=("Segoe UI", 10),
            fg=COMPLETED_FG if task.get("done") else "#222222",
            highlightthickness=2,
            highlightcolor=FOCUS_BORDER_COLOR,
            highlightbackground=bg,
        )
        if readonly:
            self.entry.config(state="readonly", readonlybackground=bg)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # col 3: star (make focusable with focus ring)
        star_idx = task.get("star", 0)
        star_color = STAR_COLORS[star_idx % len(STAR_COLORS)]
        self.star_label = tk.Label(
            self.frame, text="★", fg=star_color, bg=bg,
            font=("Segoe UI", 14),
            cursor="hand2" if not readonly else "",
            takefocus=1 if not readonly else 0,
            highlightthickness=2,
            highlightcolor=FOCUS_BORDER_COLOR,
            highlightbackground=bg,
            padx=4, pady=0,
        )
        self.star_label.pack(side=tk.LEFT, padx=2)
        if not readonly:
            self.star_label.bind("<Button-1>",
                                 lambda e: callbacks["on_star_toggle"](index))
            self.star_label.bind("<space>",
                                 lambda e: callbacks["on_star_toggle"](index))
            self.star_label.bind("<Return>",
                                 lambda e: callbacks["on_star_toggle"](index))

        # col 4: reminder (make focusable with focus ring)
        reminder_val = task.get("reminder")
        reminder_text = format_reminder(reminder_val) if reminder_val else "⏰"
        self.reminder_btn = tk.Label(
            self.frame, text=reminder_text, fg="#666666", bg=bg,
            font=("Segoe UI", 10),
            cursor="hand2" if not readonly else "",
            takefocus=1 if not readonly else 0,
            highlightthickness=2,
            highlightcolor=FOCUS_BORDER_COLOR,
            highlightbackground=bg,
            padx=4, pady=0,
        )
        self.reminder_btn.pack(side=tk.LEFT, padx=(2, 6))
        if not readonly:
            self.reminder_btn.bind("<Button-1>",
                                   lambda e: callbacks["on_reminder_click"](index))
            self.reminder_btn.bind("<space>",
                                   lambda e: callbacks["on_reminder_click"](index))
            self.reminder_btn.bind("<Return>",
                                   lambda e: callbacks["on_reminder_click"](index))

        # ordered list of focusable components in this row
        self._focusables = [self.chk, self.entry, self.star_label,
                            self.reminder_btn]

        # ---- bindings ----
        # all components: highlight row on focus
        for w in self._focusables:
            w.bind("<FocusIn>", lambda e, w=w: self._on_focus_in(w), add="+")

        if not readonly:
            # entry-specific bindings
            self.entry.bind("<FocusIn>", lambda e: callbacks["on_focus"](index),
                            add="+")
            self.entry.bind("<KeyRelease>",
                            lambda e: callbacks["on_text_change"](index, self.text_var))
            self.entry.bind("<Shift-Return>",
                            lambda e: callbacks["on_shift_enter"](index))

            # all focusable components get navigation bindings
            for w in self._focusables:
                w.bind("<Tab>", lambda e, w=w: self._tab_forward(w))
                w.bind("<Shift-Tab>", lambda e, w=w: self._tab_backward(w))
                w.bind("<Up>", lambda e: callbacks["on_up"](index))
                w.bind("<Down>", lambda e: callbacks["on_down"](index))
                w.bind("<Shift-Right>",
                       lambda e: callbacks["on_indent"](index))
                w.bind("<Shift-Left>",
                       lambda e: callbacks["on_unindent"](index))
                w.bind("<Shift-Up>",
                       lambda e: callbacks["on_move_up"](index))
                w.bind("<Shift-Down>",
                       lambda e: callbacks["on_move_down"](index))
                w.bind("<Control-d>",
                       lambda e: callbacks["on_delete"](index))

            # checkbox and star/reminder: fire on_focus for row selection
            self.chk.bind("<FocusIn>",
                          lambda e: callbacks["on_focus"](index), add="+")
            self.star_label.bind("<FocusIn>",
                                 lambda e: callbacks["on_focus"](index), add="+")
            self.reminder_btn.bind("<FocusIn>",
                                   lambda e: callbacks["on_focus"](index), add="+")

            # entry-only shortcuts
            self.entry.bind("<Control-space>",
                            lambda e: callbacks["on_toggle_done_kb"](index))
            self.entry.bind("<Alt-s>",
                            lambda e: callbacks["on_toggle_star_kb"](index))
            self.entry.bind("<Alt-r>",
                            lambda e: callbacks["on_reminder_click"](index))
        else:
            # readonly: arrow + tab navigation
            for w in self._focusables:
                w.bind("<Up>", lambda e: callbacks["on_up"](index))
                w.bind("<Down>", lambda e: callbacks["on_down"](index))
                w.bind("<Tab>", lambda e, w=w: self._tab_forward(w))
                w.bind("<Shift-Tab>", lambda e, w=w: self._tab_backward(w))

    def _on_focus_in(self, widget):
        """Highlight the row border when any component gets focus."""
        self.frame.config(highlightbackground=FOCUS_BORDER_COLOR,
                          highlightthickness=2)
        # Unhighlight when focus leaves this row entirely
        widget.bind("<FocusOut>", lambda e: self._on_focus_out(), add="+")

    def _on_focus_out(self):
        """Remove row border highlight when focus leaves."""
        # Schedule check — focus may move to another widget in same row
        self.frame.after(50, self._check_row_focus)

    def _check_row_focus(self):
        """Check if focus is still within this row."""
        try:
            focused = self.frame.focus_get()
            if focused not in self._focusables:
                self.frame.config(highlightbackground=UNFOCUS_BORDER_COLOR,
                                  highlightthickness=1)
        except Exception:
            self.frame.config(highlightbackground=UNFOCUS_BORDER_COLOR,
                              highlightthickness=1)

    def _tab_forward(self, current):
        """Move focus to next component in row, or to next row."""
        idx = self._focusables.index(current)
        if idx < len(self._focusables) - 1:
            self._focusables[idx + 1].focus_set()
        else:
            self._callbacks["on_down"](self._index)
        return "break"

    def _tab_backward(self, current):
        """Move focus to previous component in row, or to previous row."""
        idx = self._focusables.index(current)
        if idx > 0:
            self._focusables[idx - 1].focus_set()
        else:
            self._callbacks["on_up"](self._index)
        return "break"

    def set_bg(self, bg):
        self._bg = bg
        for w in (self.frame, self.entry, self.star_label, self.reminder_btn):
            w.config(bg=bg)
        # update highlight backgrounds to match
        for w in (self.chk, self.entry, self.star_label, self.reminder_btn):
            try:
                w.config(highlightbackground=bg)
            except tk.TclError:
                pass


class EmptyRow:
    """Placeholder row at the bottom for adding new tasks."""

    def __init__(self, parent, on_commit, on_up=None):
        bg = "#FAFAFA"
        self.frame = tk.Frame(parent, bg=bg, bd=0,
                              highlightthickness=1,
                              highlightbackground=UNFOCUS_BORDER_COLOR)
        self.frame.pack(fill=tk.X, padx=0, pady=0)

        self.entry = tk.Entry(self.frame, relief=tk.FLAT, bg=bg,
                              font=("Segoe UI", 10), fg="#AAAAAA",
                              highlightthickness=2,
                              highlightcolor=FOCUS_BORDER_COLOR,
                              highlightbackground=bg)
        self.entry.insert(0, "Click to add a task...")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(28, 6), pady=2)
        self.entry.bind("<FocusIn>", self._activate)
        self.entry.bind("<Return>", lambda e: on_commit(self.entry))
        if on_up:
            self.entry.bind("<Up>", lambda e: on_up())

        # row focus highlight
        self.entry.bind("<FocusIn>", lambda e: self.frame.config(
            highlightbackground=FOCUS_BORDER_COLOR, highlightthickness=2),
            add="+")
        self.entry.bind("<FocusOut>", lambda e: self.frame.config(
            highlightbackground=UNFOCUS_BORDER_COLOR, highlightthickness=1),
            add="+")

    def _activate(self, _event):
        if self.entry.get() == "Click to add a task...":
            self.entry.delete(0, tk.END)
            self.entry.config(fg="#222222")


# ---------------------------------------------------------------------------
def format_reminder(iso_str):
    try:
        dt = datetime.datetime.fromisoformat(iso_str)
        return dt.strftime("%m/%d %H:%M")
    except Exception:
        return "⏰"
