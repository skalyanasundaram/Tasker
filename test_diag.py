"""Diagnostic: test pystray and keyboard independently."""
import sys
print(f"Python: {sys.version}")

# --- Test pystray ---
print("\n--- pystray test ---")
try:
    import pystray
    from PIL import Image, ImageDraw
    print(f"pystray version: {pystray.__version__}")
    
    # Check if backend is available
    image = Image.new("RGBA", (64, 64), (68, 68, 68, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill="#4488FF")
    draw.text((24, 22), "T", fill="white")
    print(f"Icon image created OK: {image.size}")
    
    # Check what backend pystray uses on Windows
    print(f"pystray backend: {pystray.Icon.__module__}")
    
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"ERROR: {e}")

# --- Test keyboard ---
print("\n--- keyboard test ---")
try:
    import keyboard
    print(f"keyboard module loaded OK")
    print(f"keyboard version: {keyboard.version if hasattr(keyboard, 'version') else 'unknown'}")
    
    # Test if we can hook
    def test_hook(e):
        pass
    hook = keyboard.on_press(test_hook)
    keyboard.unhook(hook)
    print("keyboard.on_press hook/unhook: OK")
    
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"ERROR: {e}")

# --- Test pystray actually running ---
print("\n--- pystray run test (5 seconds) ---")
try:
    import pystray
    from PIL import Image, ImageDraw
    import threading
    import time
    
    image = Image.new("RGBA", (64, 64), (68, 68, 68, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill="#4488FF")
    
    success = {"tray_started": False}
    
    def on_setup(icon):
        success["tray_started"] = True
        print(f"  Tray icon setup callback fired! visible={icon.visible}")
    
    menu = pystray.Menu(
        pystray.MenuItem("Test", lambda icon, item: None),
    )
    icon = pystray.Icon("Test", image, "Test", menu)
    
    # pystray on Windows needs setup callback to set visible
    t = threading.Thread(target=lambda: icon.run(setup=on_setup), daemon=False)
    t.start()
    
    time.sleep(3)
    print(f"  tray_started={success['tray_started']}")
    icon.stop()
    t.join(timeout=3)
    print("  Tray icon stopped OK")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\nDone.")
