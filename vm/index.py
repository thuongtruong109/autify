import pyautogui, subprocess, time, random

name = "2022-example.com"
sock = "185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw"
address = "Louisiana"
host, port, user, passwd = (sock.split(":") + [""] * 4)[:4]
DELAY = 0.5

command = 'dir D:\\*.iso /s /b'
default_iso = r"D:\Soft\Windows_10_21H2_x64_Tiny.iso"
result = subprocess.run(command, shell=True, capture_output=True, text=True)
iso = result.stdout.strip()

if not iso:
    iso = default_iso

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

hotkey('win', 's')
type_text("virtual")
delay()
press_key("enter", sec=2)
press_key("enter")
delay(1)
hotkey('ctrl', 'n')

move_click(737, 212)
type_text(name)

move_click(800, 259)
hotkey('ctrl', 'a')
press_key("backspace")
type_text(iso)

move_click(715, 457)
move_click(1360, 317)
press_key("backspace")
type_text("4")

move_click(726, 422)
move_click(672, 318)
move_click(1139, 370)
press_key("am")
hotkey('ctrl', 'enter')

move_click(732, 483)
move_click(1008, 401, clicks=2)
move_click(1358, 401, clicks=2)
move_click(675, 489)
move_click(812, 544)
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

move_click(707, 801)
move_click(676, 427)
move_click(676, 606)

move_click(697, 830)
move_click(902, 433)

for _ in range(random.randint(1, 7)):
    press_key('down', sec=0.2)
    hotkey('ctrl', 'enter', sec=0.2)

press_key('enter')

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