import threading
import sys

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


def _create_icon_image():
    """Generate a simple 64x64 tray icon."""
    image = Image.new("RGBA", (64, 64), (68, 68, 68, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([8, 8, 56, 56], fill="#4488FF")
    draw.text((22, 18), "T", fill="white")
    return image


def create_tray_icon(on_show, on_quit):
    """Create and run the system-tray icon in a background thread.

    *on_show* and *on_quit* are zero-arg callables that schedule work
    on the Tk main thread.  Returns the ``pystray.Icon`` instance
    (or ``None`` if pystray is unavailable).
    """
    if not HAS_TRAY:
        print("[Tasker] pystray not installed – system tray disabled",
              file=sys.stderr)
        return None

    image = _create_icon_image()

    def _show(icon, item):
        on_show()

    def _quit(icon, item):
        on_quit()

    menu = pystray.Menu(
        pystray.MenuItem("Show", _show, default=True),
        pystray.MenuItem("Quit", _quit),
    )
    icon = pystray.Icon("Tasker", image, "Tasker", menu)

    def _setup(icon):
        icon.visible = True

    def _run():
        try:
            icon.run(setup=_setup)
        except Exception as e:
            print(f"[Tasker] Tray icon error: {e}", file=sys.stderr)

    t = threading.Thread(target=_run, daemon=False)
    t.start()
    return icon
