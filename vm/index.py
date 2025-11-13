import pyautogui, subprocess, time, random

name = "2022-example.com"
sock = "185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw"
address = "Louisiana"
host, port, user, passwd = (sock.split(":") + [""] * 4)[:4]

command = 'dir D:\\*.iso /s /b'
default_iso = r"D:\Soft\Windows_10_21H2_x64_Tiny.iso"
result = subprocess.run(command, shell=True, capture_output=True, text=True)
iso = result.stdout.strip()

if not iso:
    iso = default_iso

pyautogui.hotkey('win', 's')
pyautogui.typewrite("virtual")
time.sleep(1)
pyautogui.press("enter")
time.sleep(1)
pyautogui.moveTo(1060, 545, duration=1)
pyautogui.click()
time.sleep(1)
pyautogui.hotkey('ctrl', 'n')
time.sleep(1)

pyautogui.moveTo(737, 200, duration=1)
pyautogui.click()
pyautogui.typewrite(name)

pyautogui.moveTo(800, 258, duration=1)
pyautogui.click()
pyautogui.typewrite(iso)

pyautogui.moveTo(715, 457, duration=1)
pyautogui.click()

pyautogui.moveTo(1360, 312, duration=1)
pyautogui.click()
pyautogui.press("backspace")
pyautogui.typewrite("4")

pyautogui.moveTo(726, 422, duration=1)
pyautogui.click()

pyautogui.moveTo(675, 312, duration=1)
pyautogui.click()

pyautogui.moveTo(1139, 366, duration=1)
pyautogui.click()

pyautogui.moveTo(1080, 405, duration=1)
pyautogui.click()

pyautogui.moveTo(732, 483, duration=1)
pyautogui.click()

pyautogui.moveTo(1008, 397, duration=1)
pyautogui.click()
pyautogui.click()

pyautogui.moveTo(1358, 396, duration=1)
pyautogui.click()
pyautogui.click()

pyautogui.moveTo(675, 486, duration=1)
pyautogui.click()

pyautogui.moveTo(812, 532, duration=1)
pyautogui.click()
pyautogui.typewrite(host)

pyautogui.moveTo(1062, 534, duration=1)
pyautogui.click()
pyautogui.typewrite(port)

pyautogui.moveTo(836, 559, duration=1)
pyautogui.click()
pyautogui.typewrite(user)

pyautogui.moveTo(1057, 560, duration=1)
pyautogui.click()
pyautogui.typewrite(passwd)

pyautogui.moveTo(1258, 536, duration=1)
pyautogui.click()
pyautogui.typewrite("8.8.8.8")

pyautogui.moveTo(676, 710, duration=1)
pyautogui.click()

pyautogui.moveTo(777, 620, duration=1)
pyautogui.click()
pyautogui.typewrite(address)
pyautogui.sleep(1)
pyautogui.press("down")
pyautogui.press("enter")

pyautogui.moveTo(676, 763, duration=1)
pyautogui.click()

pyautogui.moveTo(912, 684, duration=1)
pyautogui.click()

pyautogui.moveTo(707, 797, duration=1)
pyautogui.click()

pyautogui.moveTo(676, 421, duration=1)
pyautogui.click()

pyautogui.moveTo(676, 600, duration=1)
pyautogui.click()

pyautogui.moveTo(697, 827, duration=1)
pyautogui.click()

n = random.randint(1, 7)

for i in range(n):
    pyautogui.press('down')
    time.sleep(0.2)

pyautogui.press('enter')

pyautogui.moveTo(1270, 876, duration=1)
pyautogui.click()