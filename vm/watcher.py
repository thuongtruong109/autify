import cv2
import numpy as np
import pyautogui
import threading
import time

class ParallelMultiWatcher:
    def __init__(self, templates, threshold=0.8, check_interval=0.5, gui_lock=None):
        """
        templates: list of dict, mỗi dict gồm:
            - 'template_path' hoặc 'template_image' (np.ndarray)
            - 'name': tên template
            - 'callback': hàm tùy chọn khi detect (nếu không có sẽ click mặc định)
        threshold: ngưỡng match
        check_interval: delay mỗi lần check
        gui_lock: threading.Lock() để tránh xung đột thao tác GUI
        """
        self.templates = templates
        self.threshold = threshold
        self.check_interval = check_interval
        self.threads = []
        self.detected_flags = {}  # lưu trạng thái đã detect từng template
        self.gui_lock = gui_lock or threading.Lock()
        self.running = False

    def _watch_screen(self, template_gray, name, callback):
        w, h = template_gray.shape[::-1]
        print(f"[Watcher-{name}] Bắt đầu theo dõi template...")

        while self.running and not self.detected_flags.get(name, False):
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)

            if loc[0].size > 0:
                pt = (loc[1][0], loc[0][0])
                x, y = pt[0] + w // 2, pt[1] + h // 2

                with self.gui_lock:
                    if callback:
                        callback(x, y, name)
                    else:
                        pyautogui.click(x, y)
                        print(f"[Watcher-{name}] Click mặc định tại ({x},{y})")

                self.detected_flags[name] = True
                break

            time.sleep(self.check_interval)

        print(f"[Watcher-{name}] Kết thúc watcher.")

    def start(self):
        """Bắt đầu tất cả watcher trong thread riêng (non-blocking)"""
        self.running = True
        for template_info in self.templates:
            name = template_info.get('name', 'Unnamed')
            callback = template_info.get('callback', None)

            # Load template
            if 'template_path' in template_info:
                template = cv2.imread(template_info['template_path'], cv2.IMREAD_UNCHANGED)
            elif 'template_image' in template_info:
                template = template_info['template_image']
            else:
                print(f"[Watcher-{name}] Không có template hợp lệ, bỏ qua")
                continue

            if template is None:
                print(f"[Watcher-{name}] Không load được template, bỏ qua")
                continue

            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            self.detected_flags[name] = False
            t = threading.Thread(
                target=self._watch_screen,
                args=(template_gray, name, callback),
                daemon=True
            )
            self.threads.append(t)
            t.start()

        print("[ParallelMultiWatcher] Tất cả watcher đã start (non-blocking).")

    def stop(self):
        """Dừng tất cả watcher"""
        self.running = False
        print("[ParallelMultiWatcher] Đang dừng tất cả watcher...")
        # không cần join các daemon thread, chúng sẽ tự kết thúc khi main thread kết thúc
