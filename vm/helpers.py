import os, sys, time
import pyautogui

def safe_exit(code=0):
    print("✅ Exit the program safely...")
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        sys.exit(code)
    except SystemExit:
        os._exit(code)

def safe_locate(img, confidence=0.7, retries=3, delay=0.15):
    for _ in range(retries):
        try:
            pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)
            if pos:
                return pos
        except Exception as e:
            print(f"[safe_locate] Error locating '{img}': {e}")
        time.sleep(delay)
    return None
