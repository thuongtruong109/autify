import pygetwindow as gw
import pyautogui
import time

pyautogui.click(200, 200)

# duyệt tất cả cửa sổ Chrome đang mở
for win in gw.getAllWindows():
    title = win.title.lower()

    # kiểm tra trang "What's New"
    if "what's new" in title or "chrome what's new" in title:
        print("Found tab:", win.title)

        # kích hoạt tab
        win.activate()
        time.sleep(0.3)  # đợi Chrome focus

        # đóng tab
        # pyautogui.hotkey('ctrl', 'w')
        pyautogui.moveTo(200, 0)  # tọa độ nút đóng tab (cần điều chỉnh theo
        print("Tab closed!")
