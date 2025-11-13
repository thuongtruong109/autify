# show_mouse_pos.py
import pyautogui
import time

print("Di chuột tới vị trí cần lấy, nhấn Ctrl-C để thoát.")
try:
    while True:
        x, y = pyautogui.position()
        print(f"\rX={x} Y={y}", end="", flush=True)
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nDone.")
