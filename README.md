# Tasker

A lightweight, keyboard-driven task manager built with Python 3 and Tkinter. Runs in the system tray with a minimalistic frameless UI.

## Features

- **Minimalistic UI** — thin custom title bar, no window chrome, appears in the bottom-right corner. Draggable and resizable.
- **Task Hierarchy** — press `Shift+Right` to indent a task as a child. Completing a parent automatically completes all children. Un-completing restores them too.
- **Star Priorities** — cycle through 6 colors (gold, red, green, blue, magenta, orange) to prioritize tasks.
- **Reminders** — inline date/time picker with spinboxes. Fires a popup notification when the reminder time is reached.
- **Active / Completed Views** — completed tasks disappear from the active view. Toggle with `Alt+C` or the title bar button. Completed tasks are shown read-only but can be unmarked to reactivate.
- **System Tray** — hides to tray on `Esc`. Double-click the tray icon to restore. Right-click for Show/Quit menu.
- **Global Hotkey** — `Ctrl+K, Ctrl+K` (chord) to show/hide from anywhere (requires admin on Windows).
- **Full Keyboard Navigation** — arrow keys, Tab between components, Shift+arrows to reorder/indent, and shortcuts for every action.
- **JSON Storage** — tasks stored in a flat, human-editable JSON file. Easy to hand-edit or sync via OneDrive/Dropbox.
- **File Sync Aware** — polls the JSON file every 60 seconds for external changes (e.g. edits from another device via OneDrive).
- **First-Run Setup** — prompts for the JSON file location on first launch.
- **Microsoft To Do Sync** — optional one-way push to a dedicated Microsoft Task List.

## Installation

```bash
pip install -r requirements.txt
```

If you prefer installing the core dependencies manually:

```bash
pip install pystray Pillow keyboard
```

If you want Microsoft To Do sync, also install:

```bash
pip install msal requests
```

### Dependencies

- `pystray` — system tray icon
- `Pillow` — tray icon image generation
- `keyboard` — global hotkey support (requires admin on Windows)
- `msal` — Microsoft Authentication Library for Graph
- `requests` — HTTP client for Microsoft Graph

## Usage

```bash
python tasker.pyw
# or
python -m tasker
```

On Windows, double-click `tasker.pyw` to launch without a console window.

> **Note:** Run as Administrator on Windows for the global hotkey (`Ctrl+K, Ctrl+K`) to work.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Up` / `Down` | Navigate between tasks |
| `Tab` / `Shift+Tab` | Navigate between row components |
| `Shift+Up` / `Shift+Down` | Reorder task (with children) |
| `Shift+Enter` | Insert new task below |
| `Shift+Right` | Indent task (make child) |
| `Shift+Left` | Un-indent task |
| `Ctrl+Space` | Toggle task complete |
| `Space` / `Enter` | Activate focused component (star, reminder) |
| `Alt+S` | Cycle star color |
| `Alt+R` | Open reminder picker |
| `Ctrl+D` | Delete task |
| `Alt+C` | Switch active / completed view |
| `Escape` | Hide to system tray |
| `Ctrl+K, Ctrl+K` | Global show/hide |
| `Alt+E` | Open settings |
| `Alt+K` | Show keybindings |

## Project Structure

```
Tasker/
├── tasker.pyw             # Launcher (double-click, no console)
├── requirements.txt       # Dependencies
├── design.md              # Design spec
└── tasker/                # Package
    ├── __init__.py
    ├── __main__.py        # python -m tasker entry point
    ├── constants.py       # Colors, paths, hotkeys, dimensions
    ├── ms_todo_sync.py    # Microsoft To Do one-way push
    ├── storage.py         # JSON load/save for config & tasks
    ├── tray.py            # System tray icon
    └── ui/
        ├── __init__.py
        ├── app.py         # Main app controller
        ├── title_bar.py   # Custom draggable title bar
        ├── task_row.py    # Task row & empty row widgets
        ├── task_list.py   # Scrollable task list container
        └── dialogs.py     # Settings, first-run & keybindings dialogs
```

## Configuration

Config is stored at `~/.tasker/config.json`. Press `Alt+E` to change the tasks file path (e.g. to a OneDrive folder for cross-device sync).

## Microsoft To Do Sync

Tasker can push your tasks into a **dedicated Microsoft To Do list** (one-way sync).

### Setup
1. Create an Azure App Registration and add **Microsoft Graph → Tasks.ReadWrite** permission
2. Copy the **Application (client) ID**
3. Open **Settings → Microsoft To Do** and paste the Client ID
4. Enable sync and choose the Task List name

The first sync opens a browser for consent and stores a token at:
`~/.tasker/ms_token_cache.json`

### Behavior
- Creates (or reuses) a task list by name (e.g. **Tasker**)
- **Clears and replaces** only that list — other lists are untouched
- Pushes: title, completion status, reminder (as due date), and starred → Important
- All tasks are pushed as plain tasks (no subtasks)
- Sync runs automatically in the background after each local update

## JSON Format

Tasks are stored as a flat list — easy to read and edit manually:

```json
[
  {"text": "Buy groceries", "done": false, "star": 1, "indent": 0, "reminder": null},
  {"text": "Get milk", "done": false, "star": 0, "indent": 1, "reminder": "2026-03-01T09:00:00"},
  {"text": "Get bread", "done": false, "star": 0, "indent": 1, "reminder": null}
]
```

## License

MIT
