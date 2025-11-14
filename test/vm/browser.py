# pip install pywin32

import pyautogui
import pyperclip
import subprocess
import time
import random
import ctypes
import win32gui

# ------------------- Cấu hình -------------------
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SEARCH_TERMS = ["python tutorial", "learn selenium", "weather today", "best coffee near me"]
RUN_SECONDS = 180  # chạy khoảng 3 phút
# -------------------------------------------------

# DPI aware để toạ độ chính xác
ctypes.windll.user32.SetProcessDPIAware()

# ---------- Human-like functions ----------
def rand_sleep(a, b):
    time.sleep(random.uniform(a, b))

def human_type(text):
    if random.random() < 0.5:
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
    else:
        for ch in text:
            pyautogui.typewrite(ch)
            time.sleep(random.uniform(0.03, 0.15))
    rand_sleep(0.2, 0.5)
    pyautogui.press('enter')

def human_scroll(page_height):
    """Scroll từ trên xuống dưới theo bước ngẫu nhiên."""
    current = 0
    while current < page_height:
        step = random.randint(200, 600)
        pyautogui.scroll(-step)
        current += step
        rand_sleep(0.5, 1.5)

def human_click_random_link(window_rect):
    """Click một link bất kỳ trên trang kết quả (giống đọc)"""
    left, top, width, height = window_rect
    x = random.randint(left + 150, left + width - 150)
    y = random.randint(top + 160, top + height - 120)
    pyautogui.moveTo(x, y, duration=random.uniform(0.3, 1.0))
    pyautogui.click()
    rand_sleep(1.5, 3.0)

# ---------- Chrome window ----------
def find_chrome_window():
    def enum_cb(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Chrome" in title or "Google Chrome" in title:
                results.append(hwnd)
    results = []
    win32gui.EnumWindows(enum_cb, results)
    return results[0] if results else None

# ---------- Main ----------
# mở Chrome nếu chưa mở
if CHROME_PATH:
    subprocess.Popen([CHROME_PATH])
    time.sleep(3)

hwnd = None
for i in range(15):
    hwnd = find_chrome_window()
    if hwnd:
        break
    time.sleep(0.5)

if not hwnd:
    print("Không tìm thấy Chrome, hãy mở thủ công rồi chạy lại.")
    exit()

rect = win32gui.GetWindowRect(hwnd)
left, top, width, height = rect

end_time = time.time() + RUN_SECONDS

while time.time() < end_time:
    term = random.choice(SEARCH_TERMS)

    # focus Chrome
    win32gui.SetForegroundWindow(hwnd)
    rand_sleep(0.5, 1.2)

    # focus omnibox
    pyautogui.hotkey('ctrl', 'l')
    rand_sleep(0.2, 0.5)
    pyautogui.hotkey('ctrl', 'a')
    rand_sleep(0.1, 0.3)

    # type search
    human_type(term)

    # scroll trang kết quả
    human_scroll(height)

    # click link ngẫu nhiên trong trang
    if random.random() < 0.6:
        human_click_random_link((left, top, width, height))
        # scroll nội dung trang link
        human_scroll(height // 2)
        # quay lại Google
        pyautogui.hotkey('alt', 'left')
        rand_sleep(1.0, 3.0)

    # nghỉ giữa các lượt search
    rand_sleep(4.0, 12.0)
