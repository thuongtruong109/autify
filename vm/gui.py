import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys

class VMAutomationLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("VM Automation - Autify")
        self.root.geometry("800x250")
        self.root.resizable(False, False)

        self.result = None
        self.cancelled = False

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

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

        self.sock_entry = ttk.Entry(input_frame, width=35, font=('Arial', 10))
        self.sock_entry.grid(row=0, column=3, padx=(0, 20))
        self.sock_entry.insert(0, "185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw")

        # Address input
        address_label = ttk.Label(input_frame, text="Address:", font=('Arial', 10, 'bold'))
        address_label.grid(row=0, column=4, padx=(0, 5), sticky=tk.W)

        self.address_entry = ttk.Entry(input_frame, width=25, font=('Arial', 10))
        self.address_entry.grid(row=0, column=5)
        self.address_entry.insert(0, "Louisiana")

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

        # Cancel button
        cancel_button = tk.Button(button_frame, text="Cancel",
                               command=self.cancel_automation,
                               bg="#f44336", fg="white",
                               font=('Arial', 11, 'bold'),
                               padx=20, pady=10,
                               cursor="hand2")
        cancel_button.grid(row=0, column=2, padx=10)

        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to start",
                                     font=('Arial', 10), foreground="gray")
        self.status_label.grid(row=3, column=0, columnspan=6, pady=(10, 0))

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

        # Store the result and close
        self.result = [name, sock, address]
        self.status_label.config(text="Starting automation...", foreground="green")
        self.root.after(500, self.root.destroy)

    def cancel_automation(self):
        """Cancel the automation"""
        self.cancelled = True
        self.result = None
        self.root.destroy()

    def clear_fields(self):
        """Clear all input fields"""
        self.name_entry.delete(0, tk.END)
        self.sock_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.status_label.config(text="Fields cleared", foreground="orange")
        self.root.after(2000, lambda: self.status_label.config(
            text="Ready to start", foreground="gray"))


def get_vm_info():
    """
    Show GUI and return user input for VM configuration
    Returns: [name, sock, address] or None if cancelled
    """
    root = tk.Tk()
    app = VMAutomationLauncher(root)
    root.mainloop()

    if app.cancelled:
        return None

    return app.result


if __name__ == "__main__":
    info = get_vm_info()
    if info:
        print("Configuration:", info)
    else:
        print("Cancelled by user")
