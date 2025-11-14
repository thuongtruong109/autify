import sys
import pyautogui, subprocess, time, random
import cv2
import numpy as np
import pyautogui
import threading
import time
import pygetwindow as gw
import pyperclip

# from watcher import ParallelMultiWatcher

# templates = [
#     {'template_path': './templates/open_chrome.png', 'name': 'Open Chrome'},
# ]

# watcher = ParallelMultiWatcher(templates, threshold=0.85)
# watcher.start()

# ################################################

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
                print(f"[Watcher] Clicked {template_path} at: {x}, {y}")
                already_clicked = True
        else:
            found_event.clear()
            already_clicked = False

        time.sleep(check_interval)

watcher_thread = threading.Thread(target=watch_screen, daemon=True)
watcher_thread.start()

# #############################################################
command = 'dir D:\\*.iso /s /b'
default_iso = r"D:\Soft\Windows_10_21H2_x64_Tiny.iso"
result = subprocess.run(command, shell=True, capture_output=True, text=True)
iso = result.stdout.strip() or default_iso
DELAY = 0.5
# #############################################################

# VM
if len(sys.argv) < 4:
    print("⚠️ Usage: python index.py <name> <sock> <address>")
    sys.exit(1)

name = sys.argv[1]
sock = sys.argv[2]
address = sys.argv[3]

host, port, user, passwd = (sock.split(":") + [""] * 4)[:4]

def delay(sec=DELAY):
    time.sleep(sec)

def move_click(x, y, sec=DELAY, clicks=1):
    pyautogui.moveTo(x, y, duration=sec)
    for _ in range(clicks):
        pyautogui.click()

def type_text(text, sec=DELAY):
    pyautogui.typewrite(text)

def press_key(key, sec=DELAY):
    pyautogui.press(key)
    delay(sec)

def hotkey(*keys, sec=DELAY):
    pyautogui.hotkey(*keys)
    delay(sec)

# hotkey('win', 'd')

# hotkey('win', 's')
# type_text("virtual")
# delay()
# press_key("enter", 3)
# press_key("enter")
# delay(1)
# hotkey('win', 'up')
# delay(1)
# hotkey('ctrl', 'n')

# # Name and Operating System
# move_click(737, 212)
# type_text(name)

# move_click(800, 259)
# hotkey('ctrl', 'a')
# press_key("backspace")
# type_text(iso)

# # Harware
# move_click(715, 457)
# move_click(1360, 317)
# press_key("backspace")
# type_text("4")

# # Preset
# move_click(726, 422)
# move_click(672, 312)
# move_click(1139, 370)
# press_key("a")
# hotkey('ctrl', 'enter')

# # Network
# move_click(732, 483)
# move_click(1008, 399, clicks=2)
# move_click(1358, 399, clicks=2)
# move_click(675, 489)
# move_click(812, 540)
# type_text(host)
# move_click(1075, 538)
# hotkey('ctrl', 'a')
# press_key("backspace")
# type_text(port)
# move_click(1258, 537)
# type_text("8.8.8.8")
# move_click(836, 562)
# type_text(user)
# move_click(1057, 563)
# type_text(passwd)
# move_click(777, 622)
# type_text(address)
# press_key("down")
# press_key("enter")
# move_click(676, 714)
# move_click(676, 767)
# move_click(912, 688)

# # AntiOS
# move_click(707, 801)
# move_click(676, 427)
# move_click(676, 606)

# # Fingerprint
# move_click(697, 830)
# move_click(902, 433)

# for _ in range(random.randint(1, 7)):
#     press_key('down', sec=0.2)
#     hotkey('ctrl', 'enter', sec=0.2)

# press_key('enter')

# # Settings
# move_click(1270, 878)
# hotkey('ctrl', 's')
# move_click(833, 382)
# move_click(900, 469)
# type_text("bi")
# hotkey('ctrl', 'enter')

# move_click(600, 427)
# move_click(873, 605)
# move_click(610, 466)
# move_click(1131, 485)
# press_key('enter')

# def wait_for_new_window(existing_windows, timeout=10):
#     end_time = time.time() + timeout
#     while time.time() < end_time:
#         current_windows = gw.getAllWindows()
#         for w in current_windows:
#             if w.title not in existing_windows and w.title.strip() != "":
#                 w.activate()
#                 delay(0.5)
#                 return w
#         delay(0.5)
#     raise Exception("No new window appeared")


# existing_windows = set(w.title for w in gw.getAllWindows())

# # Start
# pyautogui.rightClick(30, 1010, duration=DELAY)
# delay()
# move_click(75, 753)
# move_click(320, 753)

# # Mount ISO
# modal_window = wait_for_new_window(existing_windows)

# hotkey('alt', 'tab')
# delay(8)
# hotkey('alt', 'tab')
# move_click(1100, 1060, clicks=2)
# delay(2)
# pyautogui.moveTo(1079, 500, duration=0.5)
# move_click(1079, 500, clicks=5)
# type_text(iso, sec=0.1)

# search_location = pyautogui.locateCenterOnScreen('mount_iso2.png', confidence=0.8)

# if search_location:
#     pyautogui.moveTo(search_location, duration=0.3)
#     pyautogui.click()
#     print("Clicked mount iso button")
# else:
#     print("Image not found on screen.")

# for _ in range(10):
#     press_key('enter', sec=0.1)

# delay(50)
# move_click(1079, 500)
# move_click(1090, 530)
# delay(240)
# move_click(1100, 1060, clicks=2)
# delay(2)

# In the VM window
move_click(1079, 500)
# hotkey('win', 'up')
# delay(1)
# move_click(300, 800)
# move_click(1000, 444)
# for _ in range(3):
#     press_key('enter', sec=0.2)

# # move_click(989, 1072)

# Open Chrome (chưa dùng được)
# hotkey('win', 's') # move_click(30, 998)
# type_text("chrome")
# delay(1)
# press_key("enter", sec=3)
# move_click(520, 750)
# hotkey('win', 'up')
# delay(1)

# # Chrome settings (chưa dùng được)
# hotkey('ctrl', 'l')
# type_text("chrome://settings/content/location?search=pop")
# press_key('tab')
# press_key('tab')
# press_key('down')
# hotkey('ctrl', 'l')
# type_text("chrome://settings/content/popups?search=pop")
# press_key('tab')
# press_key('tab')
# press_key('up')

# # Install GoLess extension (chưa dùng được)
# hostkey('ctrl', 'l')
# type_text("https://chromewebstore.google.com/detail/goless-browser-automation/ghlmiigebgipgagnhlanjmmniefbfihl")
# press_key('tab', sec=0.2)
# press_key('tab', sec=0.2)
# press_key('tab', sec=0.2)
# press_key('tab', sec=0.2)
# press_key('tab', sec=0.2)

# press_key('enter', sec=6)
# press_key('left')
# press_key('enter')

# Turn on virtual keyboard
move_click(30, 1003)
move_click(23, 903)
delay(1)
move_click(800, 531)
pyautogui.moveTo(150, 600, duration=0.5)
pyautogui.scroll(-600)
move_click(152, 573)
move_click(414, 334)
delay(1)

def paste_into_vm(x, y, text):
    pyperclip.copy(text)
    time.sleep(0.1)

    pyautogui.click(x, y)
    time.sleep(0.2)

    move_click(341, 940)
    move_click(723, 873)
    time.sleep(0.1)

# def paste_vm(text):
#     pyperclip.copy(text)
#     time.sleep(0.1)

#     move_click(341, 940)
#     move_click(723, 873)
#     time.sleep(0.1)

def fullscreen_vm():
    move_click(430, 939)
    move_click(1306, 871)

def keyboard_vm(key):
    match key:
        case "ctrl+l":
            move_click(341, 940)
            move_click(1095, 808)
            return
        case "ctrl+v":
            move_click(341, 940)
            move_click(723, 873)
            return
        case "enter":
            move_click(1404, 808)
            return
        case _:
            return "Invalid day"

def search_vm(text):
    # move_click(341, 940)
    # move_click(1095, 808)
    keyboard_vm("ctrl+l")
    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard_vm("ctrl+v")
    # move_click(341, 940)
    # move_click(723, 873)

# Open Chrome
paste_into_vm(110, 1000, "chrome")
# move_click(1404, 808)
keyboard_vm("enter")

fullscreen_vm()
search_vm("chrome://settings/content/location?search=pop")

