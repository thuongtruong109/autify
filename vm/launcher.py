import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

class VMAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VM Automation - Autify")
        self.root.geometry("850x300")
        self.root.resizable(False, False)

        # Variables to store info
        self.info = None

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Center the window
        self.center_window()

        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="VM Automation Configuration",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=6, pady=(0, 20))

        # Input fields frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=6, pady=10)

        # Name input
        name_label = ttk.Label(input_frame, text="Name:", font=('Arial', 10, 'bold'))
        name_label.grid(row=0, column=0, padx=(0, 5), sticky=tk.W)

        self.name_entry = ttk.Entry(input_frame, width=25, font=('Arial', 10))
        self.name_entry.grid(row=0, column=1, padx=(0, 20))
        self.name_entry.insert(0, "2022-example.com")

        # Sock input
        sock_label = ttk.Label(input_frame, text="Sock:", font=('Arial', 10, 'bold'))
        sock_label.grid(row=0, column=2, padx=(0, 5), sticky=tk.W)

        self.sock_entry = ttk.Entry(input_frame, width=38, font=('Arial', 10))
        self.sock_entry.grid(row=0, column=3, padx=(0, 20))
        self.sock_entry.insert(0, "185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw")

        # Address input
        address_label = ttk.Label(input_frame, text="Address:", font=('Arial', 10, 'bold'))
        address_label.grid(row=0, column=4, padx=(0, 5), sticky=tk.W)

        self.address_entry = ttk.Entry(input_frame, width=25, font=('Arial', 10))
        self.address_entry.grid(row=0, column=5)
        self.address_entry.insert(0, "Louisiana")

        # ISO Path input row
        iso_frame = ttk.Frame(input_frame)
        iso_frame.grid(row=1, column=0, columnspan=6, pady=(10, 0), sticky=(tk.W, tk.E))

        iso_label = ttk.Label(iso_frame, text="ISO Path:", font=('Arial', 10, 'bold'))
        iso_label.grid(row=0, column=0, padx=(0, 5), sticky=tk.W)

        self.iso_entry = ttk.Entry(iso_frame, width=70, font=('Arial', 10))
        self.iso_entry.grid(row=0, column=1, padx=(0, 10))

        browse_button = tk.Button(iso_frame, text="Browse...",
                                 command=self.browse_iso,
                                 bg="#2196F3", fg="white",
                                 font=('Arial', 9, 'bold'),
                                 padx=10, pady=5,
                                 cursor="hand2")
        browse_button.grid(row=0, column=2)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=6, pady=20)

        # Start button
        self.start_button = tk.Button(button_frame, text="Start Automation",
                                      command=self.start_automation,
                                      bg="#4CAF50", fg="white",
                                      font=('Arial', 11, 'bold'),
                                      padx=20, pady=10,
                                      cursor="hand2")
        self.start_button.grid(row=0, column=0, padx=10)

        # Clear button
        clear_button = tk.Button(button_frame, text="Clear All",
                                command=self.clear_fields,
                                bg="#ff9800", fg="white",
                                font=('Arial', 11, 'bold'),
                                padx=20, pady=10,
                                cursor="hand2")
        clear_button.grid(row=0, column=1, padx=10)

        # Exit button
        exit_button = tk.Button(button_frame, text="Exit",
                               command=self.root.quit,
                               bg="#f44336", fg="white",
                               font=('Arial', 11, 'bold'),
                               padx=20, pady=10,
                               cursor="hand2")
        exit_button.grid(row=0, column=2, padx=10)

        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to start",
                                     font=('Arial', 10), foreground="gray")
        self.status_label.grid(row=3, column=0, columnspan=6, pady=(10, 0))

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def validate_inputs(self):
        """Validate input fields"""
        name = self.name_entry.get().strip()
        sock = self.sock_entry.get().strip()
        address = self.address_entry.get().strip()

        if not name:
            messagebox.showerror("Error", "Please enter a Name!")
            return False

        if not sock:
            messagebox.showerror("Error", "Please enter Sock information!")
            return False

        if not address:
            messagebox.showerror("Error", "Please enter an Address!")
            return False

        # Validate sock format (host:port:user:passwd)
        sock_parts = sock.split(":")
        if len(sock_parts) != 4:
            messagebox.showerror("Error", "Sock format should be: host:port:user:passwd")
            return False

        return True

    def start_automation(self):
        """Start the automation process"""
        if not self.validate_inputs():
            return

        name = self.name_entry.get().strip()
        sock = self.sock_entry.get().strip()
        address = self.address_entry.get().strip()
        iso_path = self.iso_entry.get().strip()

        # Store info and close window (iso_path can be empty)
        self.info = [name, sock, address, iso_path]
        self.root.quit()
        self.root.destroy()

    def browse_iso(self):
        """Open file dialog to browse for ISO file"""
        filename = filedialog.askopenfilename(
            title="Select ISO File",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if filename:
            self.iso_entry.delete(0, tk.END)
            self.iso_entry.insert(0, filename)
            self.status_label.config(text="ISO file selected", foreground="green")
            self.root.after(2000, lambda: self.status_label.config(
                text="Ready to start", foreground="gray"))

    def clear_fields(self):
        """Clear all input fields"""
        self.name_entry.delete(0, tk.END)
        self.sock_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.iso_entry.delete(0, tk.END)
        self.status_label.config(text="Fields cleared", foreground="orange")
        self.root.after(2000, lambda: self.status_label.config(
            text="Ready to start", foreground="gray"))

def get_vm_info():
    """Show GUI and get VM information"""
    root = tk.Tk()
    app = VMAutomationGUI(root)
    root.mainloop()
    return app.info

if __name__ == "__main__":
    info = get_vm_info()
    if info:
        print(f"✓ Name: {info[0]}")
        print(f"✓ Sock: {info[1]}")
        print(f"✓ Address: {info[2]}")
        print(f"✓ ISO Path: {info[3] if info[3] else '(auto-detect)'}")
    else:
        print("✗ Cancelled")
