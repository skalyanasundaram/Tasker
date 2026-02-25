import json
import os

from .constants import CONFIG_DIR, CONFIG_FILE, DEFAULT_DATA_FILE


def load_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None  # signals first run


def is_first_run():
    return not os.path.exists(CONFIG_FILE)


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def load_tasks(path):
    """Load tasks from a flat JSON list – easy to hand-edit."""
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (PermissionError, json.JSONDecodeError, OSError):
            return []
    return []


def save_tasks(path, tasks):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except (PermissionError, OSError):
        pass  # silently fail if file is locked (e.g. OneDrive sync)
