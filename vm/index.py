import sys, os, subprocess, time, random, threading
import pyautogui
import pygetwindow as gw
import pyperclip

from watcher import ScreenWatcher
from virtual_mouse import move_mouse, click_mouse, mouse_down, mouse_up
from helpers import safe_exit, safe_locate, shutdown, turn_off_capslock

pyautogui.FAILSAFE = True
sys.dont_write_bytecode = True

DELAY = 0.4
GOLESS_SUCCESS_FLAG = False

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

def start_vm():
    pyautogui.rightClick(30, 1010, duration=DELAY)
    delay(1)
    move_click(75, 753)
    move_click(320, 753)

def shutdown_vm():
    move_click(30, 1003)
    delay(1)
    move_click(30, 953)
    delay(0.8)
    move_click(30, 868)

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
    global GOLESS_SUCCESS_FLAG
    print("🟢 Goless success detected. Stopping script!")
    GOLESS_SUCCESS_FLAG = True

# Verify install chrome (some driver has this issue)
def install_chrome_callback(x, y):
    click_mouse(x, y)
    delay(35)
    move_click(396, 720)
    delay(2)
    move_click(396, 720)
    for _ in range(30):
        move_click(491, 123)
        delay(0.3)
        move_click(491, 148)
        delay(0.2)
        move_click(699, 248)
        delay(1)

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
    ScreenWatcher("./templates/update_driver_iso.png"),
    ScreenWatcher("./templates/update_driver_iso.png", min_delay=5),
    ScreenWatcher("./templates/update_driver_iso.png", min_delay=10),

    # ScreenWatcher("./templates/cancel_capture.png", min_delay=250),
    ScreenWatcher("./templates/install_software.png", callback=install_chrome_callback),
    ScreenWatcher("./templates/skip_location_vi.png"),
    ScreenWatcher("./templates/skip_location_us.png"),
    ScreenWatcher("./templates/restart_vm.png"),
    ScreenWatcher("./templates/skip_chrome_welcome.png", threshold=0.65, callback=skip_chrome_welcome_callback),
    ScreenWatcher("./templates/skip_chrome_welcome2.png", threshold=0.65, callback=skip_chrome_welcome_callback),
    ScreenWatcher("./templates/skip_AI_banner.png"),
    ScreenWatcher("./templates/skip_privacy.png"),
    ScreenWatcher("./templates/skip_privacy.png", min_delay=5),
    ScreenWatcher("./templates/goless_success.png", callback=stop_on_goless_success)
]

for w in watchers:
    w.start()

# ------------------ Load configurations -----------------
command = 'dir D:\\*.iso /s /b'
default_iso = r"D:\Windows_10_21H2_x64_Tiny.iso"
result = subprocess.run(command, shell=True, capture_output=True, text=True)

try:
    from launcher import get_vm_info
    print("🚀 Starting GUI...")
    info = get_vm_info()

    if not info:
        print("✗ Cancelled by user")
        sys.exit(0)

    rows_data = info[0]
    iso_path = info[1]
    mode = info[2]

except Exception as e:
    print(f"⚠️ GUI not available, using default values: {e}")
    rows_data = [("2022-example.com", "193.160.82.111:6083:lkqbgbdk:klwsil8ci4hw", "Louisiana")]
    iso_path = ""
    mode = "full"

if not rows_data:
    print("⚠️ No rows data")
    sys.exit(1)

# #############################################################

def open_vm_app():
    hotkey('win', 'd')
    hotkey('win', 's')
    paste("a5")
    delay(0.5)
    press_key("enter", 4)
    press_key("enter")
    delay(0.7)
    hotkey('win', 'up')

def close_vm_app():
    move_click(1902, 6)

def preset_media():
    move_click(719, 369)
    media_opt = random.choice(['c', 'f', 'g', 'i', 'l', 'm', 't'])
    press_key(media_opt)
    hotkey('ctrl', 'enter')

def preset_marketplaces():
    move_click(1139, 369)
    press_key("e")
    hotkey('ctrl', 'enter')

def preset_payment():
    move_click(1139, 432)
    press_key("p")
    hotkey('ctrl', 'enter')

def preset_misc():
    move_click(1139, 432)
    misc_opt = random.choice(['1', 't'])
    press_key(misc_opt)
    hotkey('ctrl', 'enter')

preset_switch = {
    1: preset_media,
    2: preset_marketplaces,
    3: preset_payment,
    4: preset_misc
}

def retry_locate(image_path, confidence=0.65, retries=3, delay_between=1.0, callback=None):
    for attempt in range(1, retries + 1):
        location = safe_locate(image_path, confidence=confidence)
        if location is not None:
            x, y = location
            if callback:
                callback(x, y)
            return True
        else:
            print(f"⚠ Attempt {attempt}/{retries}: {image_path} not found, retrying...")
            time.sleep(delay_between)

    print(f"⚠ {image_path} not found after all retries")
    return False

def vm_setup(name, sock, address):
    iso = iso_path if iso_path else (default_iso or result.stdout.strip())
    host, port, user, passwd = (sock.split(":") + [""] * 4)[:4]

    # Create new VM
    hotkey('ctrl', 'n')
    delay(1.2)

    def click_create_vm_modal_location(x, y):
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.mouseDown()
        pyautogui.moveTo(590, 129, duration=0.7)
        pyautogui.mouseUp()
        print("Clicked create new VM modal")

    success_1 = retry_locate('templates/create_vm.png', confidence=0.7, callback=click_create_vm_modal_location)
    if not success_1:
        return False

    # Name and Operating System
    move_click(737, 206)
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
    preset_choice = random.choice(list(preset_switch))
    preset_switch[preset_choice]()

    # Network
    move_click(732, 483)
    move_click(1008, 399, clicks=2)
    move_click(1358, 399, clicks=2)
    move_click(675, 489)
    move_click(812, 538)
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
    move_click(676, 425)
    move_click(676, 604)

    # GPU model
    move_click(697, 830)
    move_click(902, 428)

    for _ in range(random.randint(1, 7)):
        press_key('down', sec=0.2)
        hotkey('ctrl', 'enter', sec=0.2)

    # Fingerprint
    move_click(943, 467)
    for _ in range(random.randint(1, 10)):
        press_key('down', sec=0.2)
        hotkey('ctrl', 'enter', sec=0.2)

    delay(1)
    press_key('enter')

    # Settings
    move_click(1270, 878)
    delay(0.5)
    hotkey('ctrl', 's')
    delay(1.2)

    def click_setting_vm_modal_location(x, y):
        time.sleep(0.5)
        pyautogui.moveTo(x, y - 77, duration=0.3)
        pyautogui.mouseDown()
        pyautogui.moveTo(666, 273, duration=0.7)
        pyautogui.mouseUp()
        print("Clicked setting new VM modal")

    success_2 = retry_locate('templates/setting_vm.png', callback=click_setting_vm_modal_location)
    if not success_2:
        return False

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
    start_vm()

    delay(5)

    # Load iso to new VM
    for _ in range(6):
        move_click(1185, 770)

        # Click cancel captuture
        move_click(797, 249)
        delay(0.1)
        move_click(797, 274)
        move_click(1005, 374)

        press_key('right')
        press_key('enter')

    delay(50)
    move_click(1000, 500)
    move_click(1090, 530)

    delay(350)

    # Open fullsize VM window
    move_click(1100, 1060)
    move_click(1857, 89)

    # Wait install chrome
    delay(90)
    move_click(1100, 1060, clicks=2)
    delay(2)

    return True

def goless_setup():
    # In the VM window
    move_click(550, 300)

    # Unpin chrome
    pyautogui.rightClick(466, 996)
    delay(1)
    move_click(375, 951)
    delay(0.2)
    pyautogui.rightClick(466, 996)
    delay(1)
    move_click(375, 951)
    delay(1)

    # Open settings
    move_click(30, 1003)
    delay(0.8)
    move_click(23, 903)
    delay(1)

    def click_window_setting_location(x, y):
        move_mouse(x, y - 60)
        delay(0.3)
        click_mouse(x, y - 60)
        click_mouse(x, y - 60)
        delay(0.5)
        click_mouse(1002, 92)
        print("Clicked window setting modal")

    success_3 = retry_locate('templates/window_settings.png', confidence=0.7, callback=click_window_setting_location)
    if not success_3:
        return False

    # Turn on virtual keyboard
    delay(0.5)
    move_click(1220, 394)
    delay(0.5)
    move_click(30, 843)
    delay(0.5)
    move_click(365, 300)
    delay(0.8)

    def click_keyboard_location(x, y):
        move_mouse(x, y)
        delay(0.3)
        click_mouse(x, y)
        delay(0.3)
        click_mouse(x, y)
        delay(0.3)
        mouse_down()
        delay(0.8)
        move_mouse(306, 562)
        time.sleep(1)
        mouse_up()
        print("Clicked window keyboard modal")

    success_4 = retry_locate('templates/keyboard.png', confidence=0.7, callback=click_keyboard_location)
    if not success_4:
        return False

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
    delay(0.6)

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
    minimize_keyboard_vm()
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

    global GOLESS_SUCCESS_FLAG

    for _ in range(35):
        if GOLESS_SUCCESS_FLAG:
            break

        click_sock()
        open_goless_popup()
        minimize_keyboard_vm()
        delay(19)

    return True

def cleanup_after_vm():
    global GOLESS_SUCCESS_FLAG
    delay(6)
    GOLESS_SUCCESS_FLAG = False
    delay(1)
    for w in watchers:
        w.reset()
    delay(1)
    close_vm_app()
    delay(6)
    hotkey('alt', 'f4')

if mode == "vm":
    turn_off_capslock()

    for idx, (name, sock, address) in enumerate(rows_data):
        open_vm_app()
        delay(0.5)

        vm_ok = vm_setup(name, sock, address)
        if not vm_ok:
            print(f"⛔ VM {name} setup FAILED → skipping...")
            shutdown_vm()
            cleanup_after_vm()
            continue

        shutdown_vm()
        cleanup_after_vm()

    print(f"\n✅ Completed all {len(rows_data)} items!")

    safe_exit(0)

elif mode == "goless":
    turn_off_capslock()
    goless_setup()
    safe_exit(0)
else:
    turn_off_capslock()

    for idx, (name, sock, address) in enumerate(rows_data):
        open_vm_app()
        delay(0.5)

        vm_ok = vm_setup(name, sock, address)
        if not vm_ok:
            print(f"⛔ VM {name} setup FAILED → skipping...")
            cleanup_after_vm()
            continue

        goless_ok = goless_setup()
        if not goless_ok:
            print(f"⛔ Goless {name} setup FAILED → skipping...")
            shutdown_vm()
            cleanup_after_vm()
            continue

        delay(1)
        shutdown_vm()
        cleanup_after_vm()

    print(f"\n✅ Completed all {len(rows_data)} items!")
    safe_exit(0)

    shutdown()