# watcher.py
import cv2
import numpy as np
import threading
import pyautogui
import time

class ScreenWatcher:
    def __init__(self, template_path, threshold=0.8, check_interval=0.5):
        self.template_path = template_path
        self.threshold = threshold
        self.check_interval = check_interval

        # Load template
        self.template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        self.w, self.h = self.template_gray.shape[::-1]

        # Thread control
        self.found_event = threading.Event()
        self.already_clicked = False
        self.thread = threading.Thread(target=self._watch_screen, daemon=True)

    def start(self):
        """Start watching thread"""
        self.thread.start()

    def _watch_screen(self):
        while True:
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(screenshot_gray, self.template_gray, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)

            if loc[0].size > 0:
                self.found_event.set()

                if not self.already_clicked:
                    pt = (loc[1][0], loc[0][0])
                    x, y = pt[0] + self.w // 2, pt[1] + self.h // 2
                    pyautogui.click(x, y)
                    print(f"[ScreenWatcher] Clicked {self.template_path} at: {x}, {y}")
                    self.already_clicked = True
            else:
                self.found_event.clear()
                self.already_clicked = False

            time.sleep(self.check_interval)
