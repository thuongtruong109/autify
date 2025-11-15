import pyautogui
import cv2
import numpy as np
import threading
import time

class ScreenWatcher:
    def __init__(self, template_path, threshold=0.8, check_interval=0.5, min_delay=0, callback=None):
        self.template_path = template_path
        self.threshold = threshold
        self.check_interval = check_interval
        self.min_delay = min_delay
        self.callback = callback

        self.template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        self.w, self.h = self.template_gray.shape[::-1]

        self.detect_start_time = None
        self.already_clicked = False

        self.thread = threading.Thread(target=self._watch_screen, daemon=True)

    def start(self):
        self.thread.start()

    def _watch_screen(self):
        while True:
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(screenshot_gray, self.template_gray, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)

            if loc[0].size > 0:
                if self.detect_start_time is None:
                    self.detect_start_time = time.time()

                elapsed = time.time() - self.detect_start_time

                if elapsed >= self.min_delay:
                    if not self.already_clicked:
                        x = loc[1][0] + self.w // 2
                        y = loc[0][0] + self.h // 2

                        if self.callback:
                            pyautogui.moveTo(x, y)
                            self.callback(x, y)
                        else:
                            pyautogui.click(x, y)
                            print(f"[ScreenWatcher] Clicked {self.template_path} after {self.min_delay}s delay")

                        self.already_clicked = True
            else:
                self.detect_start_time = None
                self.already_clicked = False

            time.sleep(self.check_interval)
