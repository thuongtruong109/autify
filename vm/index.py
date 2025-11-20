import sys, os, time, subprocess, time, random, threading
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import pyperclip

from watcher import ScreenWatcher
from virtual_mouse import move_mouse, click_mouse, mouse_down, mouse_up

DELAY = 0.4

pyautogui.FAILSAFE = True
sys.dont_write_bytecode = True

def delay(sec=DELAY):
    time.sleep(sec)

def move_click(x, y, sec=DELAY, clicks=1):
    move_mouse(x, y)
    time.sleep(sec)
    for _ in range(clicks):
        click_mouse(x, y)

def type_text(text, sec=DELAY):
    pyautogui.typewrite(text)

def press_key(key, sec=DELAY):
    pyautogui.press(key)
    delay(sec)

def hotkey(*keys, sec=DELAY):
    pyautogui.hotkey(*keys)
    delay(sec)

def paste(text):
    pyperclip.copy(text)
    time.sleep(0.2)
    hotkey("ctrl", "a")
    press_key("backspace")
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")

def paste_into_vm(x, y, text):
    pyperclip.copy(text)
    time.sleep(0.1)

    click_mouse(x, y)
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
        case "ctrl":
            move_click(341, 940)
            return
        case "t":
            move_click(723, 745)
            return
        case _:
            return "Invalid keyboard"

def click_sock():
    move_click(417, 995)
    delay(0.5)
    move_click(660, 260)
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    keyboard_vm("enter")
    delay(0.5)
    move_click(417, 995)
    delay(1.5)
    move_click(1883, 632)

def minimize_keyboard_vm():
    delay(1)
    move_click(1624, 561)
    delay(1)
    move_click(512, 996)
    delay(1)

def search_vm(text):
    keyboard_vm("ctrl+l")
    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard_vm("ctrl+v")

def skip_chrome_welcome_callback(x, y):
    click_mouse(x, y)
    click_mouse(x, y)
    print("Found chrome welcome: ", x, y)
    delay(1)
    move_click(341, 940)
    move_click(470, 744)
    hotkey('ctrl', 'w')
    print("Clicked skip chrome welcome")

def open_goless_popup():
    move_click(1808, 103)
    delay(1)
    move_click(1560, 263)

def stop_on_goless_success(x, y):
    print(f"🟢 Goless success, stopping script!")
    os._exit(0)

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
    ScreenWatcher("./templates/skip_location_vi.png"),
    ScreenWatcher("./templates/skip_location_us.png"),
    ScreenWatcher("./templates/restart_vm.png"),
    # ScreenWatcher("./templates/skip_location_us_2.png", threshold=0.75),
    ScreenWatcher("./templates/skip_chrome_welcome.png", threshold=0.65, callback=skip_chrome_welcome_callback),
    ScreenWatcher("./templates/skip_chrome_welcome2.png", threshold=0.65, callback=skip_chrome_welcome_callback),
    ScreenWatcher("./templates/skip_AI_banner.png"),
    ScreenWatcher("./templates/skip_privacy.png"),
    ScreenWatcher("./templates/goless_success.png", callback=stop_on_goless_success)
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

mode = info[4] if len(info) > 4 else "full"

# ##############################################################

def vm_setup():
    hotkey('win', 'd')

    hotkey('win', 's')
    paste("a5")
    delay(0.5)
    press_key("enter", 4)
    press_key("enter")
    delay(0.7)
    hotkey('win', 'up')
    delay(0.5)

    # Create new VM
    hotkey('ctrl', 'n')
    delay(1)

    create_vm_location = pyautogui.locateCenterOnScreen('templates/create_vm.png', confidence=0.75)

    if create_vm_location:
        pyautogui.moveTo(create_vm_location, duration=0.3)
        pyautogui.mouseDown()
        pyautogui.moveTo(590, 129, duration=0.7)
        pyautogui.mouseUp()
        print("Clicked create new VM modal")
    else:
        print("Image not found on screen.")

    # Name and Operating System
    move_click(737, 209)
    paste(name)

    move_click(800, 259)
    paste(iso)

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
    paste(host)
    move_click(1075, 538)
    paste(port)
    move_click(1258, 537)
    type_text("8.8.8.8")
    move_click(836, 562)
    paste(user)
    move_click(1057, 563)
    paste(passwd)
    move_click(777, 622)
    paste(address)
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
    delay(1.2)

    setting_vm_location = pyautogui.locateCenterOnScreen('templates/setting_vm.png', confidence=0.65)

    if setting_vm_location:
        x, y = setting_vm_location
        delay(0.5)
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
    delay(0.5)
    hotkey('ctrl', 'enter')
    delay(1)
    move_click(650, 427)
    move_click(650, 427)
    delay(0.8)
    move_click(920, 603)
    delay(0.8)
    move_click(650, 463)
    delay(0.8)
    move_click(1176, 479)
    delay(0.6)
    press_key('enter')

    # Start
    pyautogui.rightClick(30, 1010, duration=DELAY)
    delay()
    move_click(75, 753)
    move_click(320, 753)

    delay(6)

    # Load iso to new VM
    for _ in range(6):
        move_click(1104, 770)
        move_click(797, 249)
        move_click(797, 274)
        delay(0.1)
        move_click(1005, 374)
        delay(0.1)

    delay(50)
    move_click(1000, 500)
    move_click(1090, 530)

    delay(300)

    # Open fullsize VM window
    move_click(1100, 1060)
    move_click(1857, 89)

    # Wait install chrome
    delay(80)
    move_click(1100, 1060, clicks=2)
    delay(2)

def goless_setup():
    # In the VM window
    move_click(550, 300)

    # Unpin chrome
    pyautogui.rightClick(466, 996)
    delay(1)
    move_click(375, 951)
    delay(1)

    # Open settings
    move_click(30, 1003)
    delay(0.8)
    move_click(23, 903)
    delay(1)

    setting_location = pyautogui.locateCenterOnScreen('templates/window_settings.png', confidence=0.75)

    if setting_location:
        x, y = setting_location
        move_mouse(x, y - 60)
        delay(0.3)
        click_mouse(x, y - 60)
        click_mouse(x, y - 60)
        delay(0.5)
        click_mouse(1002, 92)

        print("Clicked window setting full size modal")
    else:
        print("Image not found on screen.")

    # Turn on virtual keyboard
    delay(0.5)
    move_click(1220, 394)
    delay(0.5)
    move_click(30, 843)
    delay(0.5)
    move_click(365, 300)
    delay(0.5)

    keyboard_location = pyautogui.locateCenterOnScreen('templates/keyboard.png', confidence=0.75)

    if keyboard_location:
        move_mouse(keyboard_location[0], keyboard_location[1])
        delay(0.3)
        click_mouse(keyboard_location[0], keyboard_location[1])
        click_mouse(keyboard_location[0], keyboard_location[1])
        mouse_down()
        move_mouse(306, 562)
        time.sleep(0.7)
        mouse_up()
        print("Clicked keyboard modal")
    else:
        print("Image not found on screen.")

    # Open Chrome
    paste_into_vm(110, 1000, "chrome")
    keyboard_vm("enter")
    delay(1)
    minimize_keyboard_vm()
    delay(1)
    fullscreen_vm()
    delay(1)
    minimize_keyboard_vm()
    delay(1)
    click_sock()
    delay(1)

    # Turn off ads privacy
    keyboard_vm("ctrl")
    keyboard_vm("t")
    minimize_keyboard_vm()
    keyboard_vm("ctrl+l")
    search_vm("chrome://settings/adPrivacy")
    keyboard_vm("enter")
    delay(1)

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
    delay(1.5)
    keyboard_vm("tab")
    keyboard_vm("tab")
    keyboard_vm("down")
    minimize_keyboard_vm()

    # Turn on popup
    keyboard_vm("ctrl+l")
    search_vm("chrome://settings/content/popups?search=pop")
    keyboard_vm("enter")
    delay(1.5)
    keyboard_vm("tab")
    keyboard_vm("tab")
    keyboard_vm("up")
    minimize_keyboard_vm()

    # Install GoLess
    keyboard_vm("ctrl+l")
    search_vm("https://chromewebstore.google.com/detail/goless-browser-automation/ghlmiigebgipgagnhlanjmmniefbfihl")
    keyboard_vm("enter")
    delay(24)
    keyboard_vm("tab")
    keyboard_vm("tab")
    keyboard_vm("tab")
    keyboard_vm("tab")
    keyboard_vm("tab")
    keyboard_vm("enter")
    delay(12)
    keyboard_vm("left")
    keyboard_vm("enter")
    delay(24)
    click_sock()

    # Allow permission
    move_click(1845, 600)
    keyboard_vm("down")
    move_click(733, 504)
    delay(1.2)
    move_click(1054, 352)
    delay(1)
    move_click(1845, 600)
    delay(1)
    keyboard_vm("up")
    delay(1)

    # Login Goless
    move_click(1350, 177)
    delay(6)
    paste_into_vm(1002, 383, "AngelineliewyeStiffler620@gmail.com")
    paste_into_vm(990, 476, "Snow2511@")
    keyboard_vm("enter")
    delay(14)
    move_click(1528, 516)
    delay(1)
    move_click(1694, 154)
    move_click(1748, 154)
    delay(0.5)

    # Unpin Tab search
    pyautogui.rightClick(1805, 105)
    delay(0.8)
    move_click(1669, 144)
    delay(1)

    # Search workflows
    open_goless_popup()
    delay(6)
    move_click(1511, 210)
    paste_into_vm(1511, 210, "google")
    move_click(1748, 313)
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
    delay(1)
    move_click(1845, 600)
    pyautogui.scroll(-600)
    delay(0.6)
    keyboard_vm("win")
    keyboard_vm("down")
    delay(1)
    keyboard_vm("win")
    keyboard_vm("down")

    for _ in range(35):
        click_sock()
        open_goless_popup()
        minimize_keyboard_vm()
        delay(15)

if mode == "vm":
    vm_setup()
elif mode == "goless":
    goless_setup()
else:
    vm_setup()

    goless_setup()