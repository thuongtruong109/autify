from pywinauto import Application

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
