# mouse_tracker_gui.py
import pyautogui
import tkinter as tk

root = tk.Tk()
root.title("Mouse Pos")
label = tk.Label(root, text="", font=("Consolas", 24))
label.pack(padx=10, pady=10)

def update():
    x, y = pyautogui.position()
    label.config(text=f"X={x}  Y={y}")
    root.after(50, update)

update()
root.mainloop()
