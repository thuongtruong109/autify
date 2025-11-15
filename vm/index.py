import sys
import pyautogui, subprocess, time, random
import cv2
import numpy as np
import pyautogui
import threading
import time
import pygetwindow as gw
import pyperclip

from watcher import ScreenWatcher

DELAY = 0.5

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

def paste_into_vm(x, y, text):
    pyperclip.copy(text)
    time.sleep(0.1)

    pyautogui.click(x, y)
    time.sleep(0.2)

    move_click(341, 940)
    move_click(723, 873)
    time.sleep(0.1)

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
        case "win":
            move_click(430, 939)
            return
        case "enter":
            move_click(1404, 808)
            return
        case "tab":
            move_click(280, 742)
            return
        case "up":
            move_click(1305, 873)
            return
        case "down":
            move_click(1311, 942)
            return
        case "left":
            move_click(1228, 940)
            return
        case _:
            return "Invalid day"

def click_sock():
    move_click(417, 995)
    move_click(1079, 500)
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    move_click(417, 995)

def search_vm(text):
    keyboard_vm("ctrl+l")
    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard_vm("ctrl+v")

def skip_chrome_location_callback(x, y):
    pyautogui.click(x, y)
    pyautogui.click(x, y)
    print("Found chrome welcome: ", x, y)
    delay(1)
    move_click(341, 940)
    move_click(470, 744)
    hotkey('ctrl', 'w')
    print("Clicked skip chrome welcome")

watchers = [
    ScreenWatcher("./templates/cancel_capture.png", min_delay=180),
    ScreenWatcher("./templates/install_software.png"),
    ScreenWatcher("./templates/install_goless_vi.png"),
    ScreenWatcher("./templates/skip_location_vi.png", threshold=0.75),
    ScreenWatcher("./templates/skip_location_us.png", threshold=0.75),
    # ScreenWatcher("./sample.png", threshold=0.75),
    ScreenWatcher("./templates/skip_chrome_welcome1.png", threshold=0.6, callback=skip_chrome_location_callback),
    ScreenWatcher("./templates/skip_chrome_welcome2.png", threshold=0.6, callback=skip_chrome_location_callback)
]

for w in watchers:
    w.start()

# #############################################################
command = 'dir D:\\*.iso /s /b'
default_iso = r"D:\Soft\Windows_10_21H2_x64_Tiny.iso"
result = subprocess.run(command, shell=True, capture_output=True, text=True)
iso = result.stdout.strip() or default_iso
# #############################################################
if len(sys.argv) < 4:
    print("⚠️ Usage: python index.py <name> <sock> <address>")
    sys.exit(1)

name = sys.argv[1]
sock = sys.argv[2]
address = sys.argv[3]
host, port, user, passwd = (sock.split(":") + [""] * 4)[:4]
# ##############################################################

hotkey('win', 'd')

hotkey('win', 's')
type_text("virtual")
delay(1)
press_key("enter", 4)
press_key("enter")
delay(1)
hotkey('win', 'up')
delay(1)
hotkey('ctrl', 'n')
delay(1)

# Name and Operating System
move_click(737, 212)
delay()
type_text(name)

move_click(800, 259)
hotkey('ctrl', 'a')
press_key("backspace")
type_text(iso)

# Harware
move_click(715, 457)
move_click(1360, 317)
press_key("backspace")
type_text("4")

# Preset
move_click(726, 422)
move_click(672, 312)
move_click(1139, 370)
press_key("a")
hotkey('ctrl', 'enter')

# Network
move_click(732, 483)
move_click(1008, 399, clicks=2)
move_click(1358, 399, clicks=2)
move_click(675, 489)
move_click(812, 540)
type_text(host)
move_click(1075, 538)
hotkey('ctrl', 'a')
press_key("backspace")
type_text(port)
move_click(1258, 537)
type_text("8.8.8.8")
move_click(836, 562)
type_text(user)
move_click(1057, 563)
type_text(passwd)
move_click(777, 622)
type_text(address)
press_key("down")
press_key("enter")
move_click(676, 714)
move_click(676, 767)
move_click(912, 688)

# AntiOS
move_click(707, 801)
move_click(676, 427)
move_click(676, 606)

# Fingerprint
move_click(697, 830)
move_click(902, 433)

for _ in range(random.randint(1, 7)):
    press_key('down', sec=0.2)
    hotkey('ctrl', 'enter', sec=0.2)

delay(1)
press_key('enter')

# Settings
move_click(1270, 878)
hotkey('ctrl', 's')
move_click(833, 382)
move_click(900, 469)
type_text("bi")
hotkey('ctrl', 'enter')

move_click(600, 427)
move_click(873, 605)
move_click(610, 466)
move_click(1131, 485)
press_key('enter')

def wait_for_new_window(existing_windows, timeout=10):
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_windows = gw.getAllWindows()
        for w in current_windows:
            if w.title not in existing_windows and w.title.strip() != "":
                w.activate()
                delay(0.5)
                return w
        delay(0.5)
    raise Exception("No new window appeared")


existing_windows = set(w.title for w in gw.getAllWindows())

# Start
pyautogui.rightClick(30, 1010, duration=DELAY)
delay()
move_click(75, 753)
move_click(320, 753)

# Mount ISO
modal_window = wait_for_new_window(existing_windows)

hotkey('alt', 'tab')
delay(8)
hotkey('alt', 'tab')
move_click(1100, 1060, clicks=2)
delay(2)
pyautogui.moveTo(1079, 500, duration=0.5)
move_click(1079, 500, clicks=5)
type_text(iso, sec=0.1)

search_location = pyautogui.locateCenterOnScreen('templates/mount_iso.png', confidence=0.8)

if search_location:
    pyautogui.moveTo(search_location, duration=0.3)
    pyautogui.click()
    print("Clicked mount iso button")
else:
    print("Image not found on screen.")

for _ in range(10):
    press_key('enter', sec=0.1)

delay(50)
move_click(1079, 500)
move_click(1090, 530)
delay(240)
move_click(1100, 1060, clicks=2)
delay(2)

# Open fullsize VM window
move_click(1857, 89)

# In the VM window
move_click(550, 300)

# Open settings
move_click(30, 1003)
move_click(23, 903)
delay(1)

setting_location = pyautogui.locateCenterOnScreen('templates/window_settings.png', confidence=0.75)

if setting_location:
    x, y = setting_location
    pyautogui.moveTo(x, y - 60, duration=0.3)
    pyautogui.click()
    pyautogui.click()
    print("Clicked window setting full size modal")
else:
    print("Image not found on screen.")

# Turn on virtual keyboard
move_click(1220, 394)
move_click(30, 843)
move_click(365, 300)
delay(1)

keyboard_location = pyautogui.locateCenterOnScreen('templates/keyboard.png', confidence=0.75)

if keyboard_location:
    pyautogui.moveTo(keyboard_location, duration=0.3)
    pyautogui.click()
    pyautogui.click()
    pyautogui.mouseDown()
    pyautogui.moveTo(306, 562, duration=0.7)
    pyautogui.mouseUp()
    print("Clicked keyboard modal")
else:
    print("Image not found on screen.")

# Open Chrome
paste_into_vm(110, 1000, "chrome")
keyboard_vm("enter")
fullscreen_vm()

# Turn off location
search_vm("chrome://settings/content/location?search=pop")
keyboard_vm("enter")
delay(1)
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("down")

# Turn on popup
keyboard_vm("ctrl+l")
search_vm("chrome://settings/content/popups?search=pop")
keyboard_vm("enter")
delay(1)
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("up")
click_sock()

# Install GoLess
keyboard_vm("ctrl+l")
search_vm("https://chromewebstore.google.com/detail/goless-browser-automation/ghlmiigebgipgagnhlanjmmniefbfihl")
keyboard_vm("enter")
delay(16)
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("enter")
delay(8)
keyboard_vm("left")
keyboard_vm("enter")
delay(24)

# Allow permission
keyboard_vm("down")
move_click(733, 504)
keyboard_vm("left")
keyboard_vm("enter")
keyboard_vm("up")

# Login Goless
move_click(1350, 177)
delay(6)
paste_into_vm(1002, 383, "AngelineliewyeStiffler620@gmail.com")
paste_into_vm(990, 476, "Snow2511@")
keyboard_vm("enter")
delay(10)
move_click(1528, 516)
move_click(1718, 103)
move_click(1648, 258)
move_click(1679, 105)
delay(6)
move_click(1423, 210)
paste_into_vm(1423, 210, "google")
move_click(1657, 309)
click_sock()

# Run Goless
delay(10)
click_sock()

# Open new window and search
move_click(341, 940)
move_click(891, 880)
search_vm("https://www.shopify.com/")
keyboard_vm("enter")
move_click(1845, 600)
pyautogui.scroll(-600)
keyboard_vm("win")
keyboard_vm("down")
keyboard_vm("win")
keyboard_vm("down")

for _ in range(35):
    click_sock()
    delay(15)