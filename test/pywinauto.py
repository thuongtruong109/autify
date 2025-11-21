from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto.timings import wait_until
import time

DELAY = 0.4

def delay(sec=DELAY):
    time.sleep(sec)

# ---------------- Configuration ----------------
vm_app_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\A5 Patreon Premium Edition (August 2025 BETA 2)"  # Thay bằng đường dẫn phần mềm VM
name = "MyVM"  # Tên VM
iso = r"D:\Soft\Windows_10_21H2_x64_Tiny.iso"  # ISO mặc định

# ---------------- Launch VM Manager ----------------
app = Application(backend="uia").start(vm_app_path)

# Đợi cửa sổ chính xuất hiện
vm_window = app.window(title_re=".*VM Manager.*")  # Chỉnh regex cho đúng title cửa sổ
vm_window.wait("visible", timeout=20)
vm_window.set_focus()
delay(1)

# ---------------- Create New VM ----------------
try:
    new_vm_btn = vm_window.child_window(title="New VM", control_type="Button")
    new_vm_btn.wait('enabled', timeout=10)
    new_vm_btn.click_input()
    print("✅ Clicked 'New VM' button")
except Exception as e:
    print(f"❌ Failed to click 'New VM': {e}")

delay(1)

# ---------------- Name and Operating System ----------------
try:
    # Điền tên VM
    name_input = vm_window.child_window(auto_id="txtName")  # Thay auto_id bằng inspect tool
    name_input.wait('enabled', timeout=10)
    name_input.set_text(name)
    print(f"✅ Set VM name: {name}")

    delay(0.5)

    # Điền đường dẫn ISO
    iso_input = vm_window.child_window(auto_id="txtISO")  # Thay auto_id bằng inspect tool
    iso_input.wait('enabled', timeout=10)
    iso_input.set_text(iso)
    print(f"✅ Set ISO path: {iso}")

except Exception as e:
    print(f"❌ Failed to set name or ISO: {e}")

# ---------------- Optional: bring focus and verify ----------------
vm_window.set_focus()
delay(1)
print("🚀 VM creation setup done up to Name and Operating System")

# ------------------- Notepad -----------------------------------
app = Application(backend="uia").start("notepad.exe")

win = app.window(title_re=".*Notepad")

# Gõ nội dung
win.Edit.type_keys("Save this text.", with_spaces=True)

# Mở menu File → Save As
win.menu_select("File->Save As")

# Cửa sổ Save As
save_dialog = app.window(title="Save As")

# Gõ tên file
save_dialog.Edit.type_keys("example.txt", with_spaces=True)

# Click nút Save
save_dialog.Save.click()

