import pyautogui
import cv2
import numpy as np
import threading
import time

class ScreenWatcher:
    def __init__(self, template_path, threshold=0.8, check_interval=0.5, skip_count=0, callback=None):
        self.template_path = template_path
        self.threshold = threshold
        self.check_interval = check_interval
        self.skip_count = skip_count
        self.callback = callback

        self.template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        self.w, self.h = self.template_gray.shape[::-1]

        self.detect_count = 0
        self.already_clicked = False

        self.thread = threading.Thread(target=self._watch_screen, daemon=True)

    def reset(self):
        self.detect_count = 0
        self.already_clicked = False

    def start(self):
        self.thread.start()

    def _watch_screen(self):
        template_visible = False  # flag kiểm tra template có đang hiển thị

        while True:
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(screenshot_gray, self.template_gray, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)

            if loc[0].size > 0:
                if self.skip_count > 0:
                    # skip_count mode
                    if not template_visible:
                        self.detect_count += 1  # chỉ tăng khi template mới xuất hiện

                    template_visible = True

                    if self.detect_count >= self.skip_count + 1:
                        x = loc[1][0] + self.w // 2
                        y = loc[0][0] + self.h // 2

                        if self.callback:
                            from virtual_mouse import move_mouse
                            move_mouse(x, y)
                            self.callback(x, y)
                        else:
                            pyautogui.click(x, y)
                            print(f"[ScreenWatcher] Clicked {self.template_path} at detection #{self.detect_count}")

                        # KHÔNG reset detect_count, chỉ reset khi gọi reset()
                else:
                    # single-click mode
                    if not self.already_clicked:
                        x = loc[1][0] + self.w // 2
                        y = loc[0][0] + self.h // 2

                        if self.callback:
                            from virtual_mouse import move_mouse
                            move_mouse(x, y)
                            self.callback(x, y)
                        else:
                            pyautogui.click(x, y)
                            print(f"[ScreenWatcher] Clicked {self.template_path} (single-click mode)")

                        self.already_clicked = True

            else:
                template_visible = False  # template biến mất

            time.sleep(self.check_interval)
