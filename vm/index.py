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

DELAY = 0.4

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
        case "shift":
            move_click(317, 875)
            return
        case _:
            return "Invalid keyboard"

def click_sock():
    move_click(417, 995)
    move_click(660, 260)
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    move_click(417, 995)

def minimize_keyboard_vm():
    delay(1)
    move_click(1624, 561)
    delay(1)
    move_click(565, 996)
    delay(1)

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

# ---------------- Auto-close Chrome welcome ----------------
def auto_close_chrome_tabs():
    TARGET_TITLES = [
        "có gì mới", "chrome có gì mới",
        "what's new", "chrome what's new"
    ]
    print("🟢 Auto-close 'Có gì mới / What's New' thread started")
    while True:
        try:
            for win in gw.getAllWindows():
                title = win.title.lower().strip()
                if any(t in title for t in TARGET_TITLES):
                    print(f"⚡ Found Chrome welcome tab: {win.title}")
                    try:
                        win.activate()
                        time.sleep(0.2)
                        keyboard_vm("ctrl")
                        move_click(470, 746)
                        pyautogui.hotkey('ctrl', 'w')
                        print("✅ Tab closed!")
                    except Exception as e:
                        print(f"❌ Error closing tab: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error in auto-close thread: {e}")
            time.sleep(1)

threading.Thread(target=auto_close_chrome_tabs, daemon=True).start()
# ------------------------------------------------------------

watchers = [
    ScreenWatcher("./templates/cancel_capture.png", min_delay=180),
    ScreenWatcher("./templates/install_software.png"),
    ScreenWatcher("./templates/skip_location_vi.png", threshold=0.75),
    ScreenWatcher("./templates/skip_location_us.png", threshold=0.75),
    # ScreenWatcher("./templates/skip_location_us_2.png", threshold=0.75),
    ScreenWatcher("./templates/skip_chrome_welcome1.png", threshold=0.65, callback=skip_chrome_location_callback),
    ScreenWatcher("./templates/skip_chrome_welcome2.png", threshold=0.65, callback=skip_chrome_location_callback),
    ScreenWatcher("./templates/skip_AI_banner.png", threshold=0.65),
    ScreenWatcher("./templates/skip_privacy.png", threshold=0.75)
]

for w in watchers:
    w.start()

# #############################################################
command = 'dir D:\\*.iso /s /b'
default_iso = r"D:\Soft\Windows_10_21H2_x64_Tiny.iso"
result = subprocess.run(command, shell=True, capture_output=True, text=True)

try:
    from launcher import get_vm_info
    print("🚀 Starting GUI...")
    info = get_vm_info()

    if not info:
        print("✗ Cancelled by user")
        sys.exit(0)

except Exception as e:
    print(f"⚠️ GUI not available, using default values: {e}")
    info = ["2022-example.com", "193.160.82.111:6083:lkqbgbdk:klwsil8ci4hw", "Louisiana", ""]

if len(info) < 3:
    print("⚠️ Lack of infomation: <name> <sock> <address>")
    sys.exit(1)

# #############################################################

name = info[0]
sock = info[1]
address = info[2]
iso_path = info[3] if len(info) > 3 else ""

iso = iso_path if iso_path else (result.stdout.strip() or default_iso)
host, port, user, passwd = (sock.split(":") + [""] * 4)[:4]

# ##############################################################

hotkey('win', 'd')

hotkey('win', 's')
type_text("a5")
delay(1)
press_key("enter", 4)
press_key("enter")
delay(1)
hotkey('win', 'up')
delay(1)

# Create new VM
hotkey('ctrl', 'n')
delay(1)

create_vm_location = pyautogui.locateCenterOnScreen('templates/create_vm.png', confidence=0.75)

if create_vm_location:
    pyautogui.moveTo(create_vm_location, duration=0.3)
    pyautogui.mouseDown()
    pyautogui.moveTo(590, 130, duration=0.7)
    pyautogui.mouseUp()
    print("Clicked create new VM modal")
else:
    print("Image not found on screen.")

# Name and Operating System
move_click(737, 210)
delay(1)
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

setting_vm_location = pyautogui.locateCenterOnScreen('templates/setting_vm.png', confidence=0.65)

if setting_vm_location:
    x, y = setting_vm_location
    pyautogui.moveTo(x, y - 77, duration=0.3)
    pyautogui.mouseDown()
    pyautogui.moveTo(666, 273, duration=0.7)
    pyautogui.mouseUp()
    print("Clicked setting new VM modal")
else:
    print("Image not found on screen.")

move_click(648, 351)
move_click(880, 379)
move_click(945, 463)
type_text("bi")
hotkey('ctrl', 'enter')

move_click(650, 427)
move_click(920, 603)
move_click(650, 463)
move_click(1176, 479)
press_key('enter')

# Start
pyautogui.rightClick(30, 1010, duration=DELAY)
delay()
move_click(75, 753)
move_click(320, 753)

delay(50)
move_click(1000, 500)
move_click(1090, 530)
delay(380)
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
click_sock()
minimize_keyboard_vm()

Turn off ads privacy
keyboard_vm("ctrl+l")
search_vm("chrome://settings/adPrivacy")
keyboard_vm("enter")
minimize_keyboard_vm()

keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("enter")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("enter")
keyboard_vm("shift")
keyboard_vm("tab")
keyboard_vm("shift")
keyboard_vm("tab")
keyboard_vm("enter")

keyboard_vm("tab")
keyboard_vm("enter")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("enter")
keyboard_vm("shift")
keyboard_vm("tab")
keyboard_vm("shift")
keyboard_vm("tab")
keyboard_vm("enter")

keyboard_vm("tab")
keyboard_vm("enter")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("enter")
click_sock()
minimize_keyboard_vm()

# Turn off flags
search_vm("chrome://flags/")
keyboard_vm("enter")
delay(1)
keyboard_vm("tab")
keyboard_vm("enter")
delay(2)
click_sock()
minimize_keyboard_vm()

# Turn off location
search_vm("chrome://settings/content/location?search=pop")
keyboard_vm("enter")
delay(1)
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("down")
minimize_keyboard_vm()

# Turn on popup
keyboard_vm("ctrl+l")
search_vm("chrome://settings/content/popups?search=pop")
keyboard_vm("enter")
delay(1)
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("up")
click_sock()
minimize_keyboard_vm()

# Install GoLess
keyboard_vm("ctrl+l")
search_vm("https://chromewebstore.google.com/detail/goless-browser-automation/ghlmiigebgipgagnhlanjmmniefbfihl")
keyboard_vm("enter")
delay(22)
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("tab")
keyboard_vm("enter")
delay(10)
keyboard_vm("left")
keyboard_vm("enter")
delay(24)
click_sock()

# Allow permission
keyboard_vm("down")
move_click(733, 504)
keyboard_vm("left")
keyboard_vm("enter")
delay(6)
keyboard_vm("up")

# Login Goless
move_click(1350, 177)
delay(6)
paste_into_vm(1002, 383, "AngelineliewyeStiffler620@gmail.com")
paste_into_vm(990, 476, "Snow2511@")
keyboard_vm("enter")
delay(14)
move_click(1528, 516)

# # Turn off tab search
# pyautogui.rightClick(1807, 105)
# move_click(1670, 148)

# Search workflows
move_click(1752, 103)
move_click(1560, 263)
delay(6)
move_click(1511, 210)
paste_into_vm(1511, 210, "google")
move_click(1748, 309)
click_sock()

# Run Goless
delay(10)
click_sock()
minimize_keyboard_vm()

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