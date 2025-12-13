import ctypes
import time

# Define necessary structures and constants
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE = 0x8000

def send_input(*inputs):
    nInputs = len(inputs)
    LPINPUT = Input * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = ctypes.c_int(ctypes.sizeof(Input))
    return ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)

def move_mouse(x, y):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    abs_x = int(x * 65535 / screen_width)
    abs_y = int(y * 65535 / screen_height)
    mi = MouseInput(abs_x, abs_y, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
    ii = Input_I(mi=mi)
    inp = Input(INPUT_MOUSE, ii)
    send_input(inp)

def click_mouse(x, y, button='left'):
    move_mouse(x, y)
    time.sleep(0.01)
    if button == 'left':
        mi_down = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
        mi_up = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)
    elif button == 'right':
        mi_down = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, None)
        mi_up = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, None)
    ii_down = Input_I(mi=mi_down)
    ii_up = Input_I(mi=mi_up)
    inp_down = Input(INPUT_MOUSE, ii_down)
    inp_up = Input(INPUT_MOUSE, ii_up)
    send_input(inp_down, inp_up)

def scroll_mouse(delta):
    mi = MouseInput(0, 0, delta, MOUSEEVENTF_WHEEL, 0, None)
    ii = Input_I(mi=mi)
    inp = Input(INPUT_MOUSE, ii)
    send_input(inp)

def mouse_down(button='left'):
    if button == 'left':
        mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
    elif button == 'right':
        mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, None)
    ii = Input_I(mi=mi)
    inp = Input(INPUT_MOUSE, ii)
    send_input(inp)

def mouse_up(button='left'):
    if button == 'left':
        mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)
    elif button == 'right':
        mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, None)
    ii = Input_I(mi=mi)
    inp = Input(INPUT_MOUSE, ii)
    send_input(inp)