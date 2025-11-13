import pyautogui
import time

# Đợi vài giây để bạn chuyển sang màn hình chính
time.sleep(2)

# Tìm vị trí nút Search dựa trên hình ảnh
search_location = pyautogui.locateCenterOnScreen('search_btn.png', confidence=0.8)

if search_location:
    print("Tìm thấy nút Search tại:", search_location)
    pyautogui.moveTo(search_location, duration=0.3)
    pyautogui.click()

    # Gõ chữ cần tìm
    pyautogui.typewrite("notepad", interval=0.1)
    pyautogui.press("enter")
else:
    print("Không tìm thấy nút Search. Hãy kiểm tra ảnh mẫu hoặc độ sáng màn hình.")
