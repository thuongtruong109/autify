import ctypes
import os, sys, time, subprocess
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

def shutdown():
    subprocess.run(["shutdown", "/s", "/t", "0"], check=True)

def turn_off_capslock():
    caps_lock_state = ctypes.windll.user32.GetKeyState(0x14)

    if caps_lock_state & 1:
        ctypes.windll.user32.keybd_event(0x14, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x14, 0, 2, 0)
        print("Caps Lock has been turned off.")
    else:
        print("Caps Lock is already off.")