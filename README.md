### Isolation environment (optional)

```bash
python -m venv automation-env
```

```bash
source automation-env/bin/activate  # On Mac/Linux
automation-env\Scripts\activate  # On Windows
```

### Install packages (for VM)

```bash
pip install pyautogui
pip install numpy
pip install opencv-python
pip install pillow
```

### Install packages (for Store)

```bash
pip install selenium
pip install webdriver-manager
```

<!-- input("Đã xảy ra lỗi cần đóng và chạy lại...")
pyautogui.scroll(-300)
pyautogui.scroll(300)
pyautogui.doubleClick()
pyautogui.write('Automation_Guide.txt', interval=0.1) -->
