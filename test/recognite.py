import cv2
import numpy as np
import pyautogui
import threading
import time

template_path = "./templates/install_software.png"
threshold = 0.8
check_interval = 0.5

template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
w, h = template_gray.shape[::-1]

found_event = threading.Event()
already_clicked = False

def watch_screen():
    global already_clicked
    while True:
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        if loc[0].size > 0:
            found_event.set()
            if not already_clicked:
                pt = (loc[1][0], loc[0][0])
                x, y = pt[0] + w//2, pt[1] + h//2
                pyautogui.click(x, y)
                # print(f"[Watcher] Đã tìm thấy và click tại: {x}, {y}")
                already_clicked = True
        else:
            found_event.clear()
            already_clicked = False

        time.sleep(check_interval)

watcher_thread = threading.Thread(target=watch_screen, daemon=True)
watcher_thread.start()

for i in range(20):
    if found_event.is_set():
        print(f"[Main Task] Đã tìm thấy!")
    else:
        print(f"[Main Task] Chưa tìm thấy.")
    time.sleep(1)
