import os

# Star colors: index 0 = unlit (gray), 1-6 = lit colors
STAR_COLORS = [
    "#888888", "#FFD700", "#FF4444", "#44FF44",
    "#4488FF", "#FF44FF", "#FF8800",
]

SELECTED_ROW_BG = "#E0E8FF"
DEFAULT_ROW_BG = "#FFFFFF"
COMPLETED_FG = "#AAAAAA"
COMPLETED_ROW_BG = "#F0F0F0"
REMINDER_FLASH_BG = "#FFEEAA"
FOCUS_BORDER_COLOR = "#4488FF"
UNFOCUS_BORDER_COLOR = "#E0E0E0"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".tasker")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_DATA_FILE = os.path.join(CONFIG_DIR, "tasks.json")

GLOBAL_HOTKEY = "ctrl+k"  # chord: Ctrl+K, Ctrl+K
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 400
TITLE_HEIGHT = 24
REMINDER_CHECK_MS = 30000
