import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

from states import US_STATES

class VMAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Autify")
        self.root.geometry("530x440")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        # Variables to store info
        self.info = None

        # US States list
        self.us_states = US_STATES

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'),
                       foreground="#2c3e50", background="#f5f5f5")
        style.configure('Field.TLabel', font=('Segoe UI', 10, 'bold'),
                       foreground="#34495e", background="#f5f5f5")
        style.configure('TEntry', font=('Segoe UI', 10), padding=8)
        style.configure('TCombobox', font=('Segoe UI', 10), padding=8)
        style.configure('Card.TFrame', background="#ffffff", relief="flat")
        style.configure('Main.TFrame', background="#f5f5f5")

        # Center the window
        self.center_window()

        # Main frame
        main_frame = ttk.Frame(root, padding="10", style='Main.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title with icon
        # title_label = ttk.Label(main_frame, text="🖥️ Virtual Machine Automation",
        #                         style='Title.TLabel')
        # title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Status label with better styling - right under header
        status_frame = ttk.Frame(main_frame, style='Card.TFrame', relief="solid", borderwidth=1)
        status_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(status_frame,
                                     text="❌ Chú ý: Chuyển Unikey sang tiếng Anh trước khi chạy.\n Và không được di chuyển chuột khi tool đang chạy.\n Khi load ISO phải nhấn Enter thủ công",
                                     font=('Segoe UI', 10, 'bold'),
                                     foreground="white",
                                     background="red",
                                     padding=(10, 5))
        self.status_label.pack(fill=tk.X)

        # Card frame for inputs
        card_frame = ttk.Frame(main_frame, padding="25", style='Card.TFrame',
                              relief="solid", borderwidth=1)
        card_frame.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))

        # Name section
        name_label = ttk.Label(card_frame, text="Name:", style='Field.TLabel')
        name_label.grid(row=0, column=0, padx=(0, 10), pady=(0, 15), sticky=tk.W)
        self.name_entry = ttk.Entry(card_frame, width=50, font=('Segoe UI', 10))
        self.name_entry.grid(row=0, column=1, pady=(0, 15), sticky=(tk.W, tk.E))
        self.name_entry.insert(0, "2022-example.com")

        # Sock section
        sock_label = ttk.Label(card_frame, text="Sock:", style='Field.TLabel')
        sock_label.grid(row=1, column=0, padx=(0, 10), pady=(0, 15), sticky=tk.W)
        self.sock_entry = ttk.Entry(card_frame, width=50, font=('Segoe UI', 10))
        self.sock_entry.grid(row=1, column=1, pady=(0, 15), sticky=(tk.W, tk.E))
        self.sock_entry.insert(0, "185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw")

        # Address section
        address_label = ttk.Label(card_frame, text="Address:", style='Field.TLabel')
        address_label.grid(row=2, column=0, padx=(0, 10), pady=(0, 15), sticky=tk.W)
        address_frame = ttk.Frame(card_frame)
        address_frame.grid(row=2, column=1, pady=(0, 15), sticky=(tk.W, tk.E))
        self.address_entry = ttk.Entry(address_frame, width=38, font=('Segoe UI', 10))
        self.address_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.address_entry.insert(0, "Baton Rouge, Louisiana")
        self.address_dropdown_btn = tk.Button(address_frame, text="▼", width=2,
                                             command=self.toggle_address_dropdown,
                                             bg="#f0f0f0", fg="black", font=('Segoe UI', 8),
                                             relief="flat", cursor="hand2")
        self.address_dropdown_btn.grid(row=0, column=1, padx=(10, 10))
        address_frame.columnconfigure(0, weight=1)

        # Custom dropdown variables
        self.address_dropdown = None
        self.address_listbox = None

        # Add autocomplete functionality
        self.address_entry.bind('<KeyRelease>', self.on_address_keyrelease)
        self.address_entry.bind('<FocusOut>', self.on_address_focus_out)
        self.address_entry.bind('<Escape>', self.hide_address_dropdown)

        # ISO Path section
        iso_label = ttk.Label(card_frame, text="ISO Path:", style='Field.TLabel')
        iso_label.grid(row=3, column=0, padx=(0, 10), pady=(0, 15), sticky=tk.W)
        iso_frame = ttk.Frame(card_frame)
        iso_frame.grid(row=3, column=1, pady=(0, 15), sticky=(tk.W, tk.E))
        self.iso_entry = ttk.Entry(iso_frame, width=38, font=('Segoe UI', 10), foreground='grey')
        self.iso_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.iso_entry.insert(0, "Có thể để trống")
        # Bind events for placeholder behavior
        self.iso_entry.bind('<FocusIn>', self.on_iso_focus_in)
        self.iso_entry.bind('<FocusOut>', self.on_iso_focus_out)
        browse_button = tk.Button(iso_frame, text="📁 Browse",
                                 command=self.browse_iso,
                                 bg="#3498db", fg="white",
                                 font=('Segoe UI', 9, 'bold'),
                                 width=10,
                                 cursor="hand2",
                                 relief="flat",
                                 )
        browse_button.grid(row=0, column=1, padx=(10, 10))
        iso_frame.columnconfigure(0, weight=1)

        # Configure grid weights for responsive layout
        card_frame.columnconfigure(1, weight=1)
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.grid(row=6, column=0, columnspan=1, pady=10)

        # Start button
        self.start_button = tk.Button(button_frame, text="▶ Start Automation",
                                      command=self.start_automation,
                                      bg="#27ae60", fg="white",
                                      font=('Segoe UI', 11, 'bold'),
                                      padx=24, pady=3,
                                      cursor="hand2",
                                      relief="flat",
                                      activebackground="#229954",
                                      activeforeground="white")
        self.start_button.grid(row=0, column=1, padx=8)

        # Clear button
        clear_button = tk.Button(button_frame, text="🗑️ Clear All",
                                command=self.clear_fields,
                                bg="#e67e22", fg="white",
                                font=('Segoe UI', 11, 'bold'),
                                padx=24, pady=3,
                                cursor="hand2",
                                relief="flat",
                                activebackground="#d35400",
                                activeforeground="white")
        clear_button.grid(row=0, column=2, padx=8)

        # Configure button frame for centering
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(3, weight=1)

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def on_address_keyrelease(self, event):
        """Filter address dropdown based on user input and show custom dropdown"""
        # Ignore modifier keys
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                            'Caps_Lock', 'Num_Lock', 'Scroll_Lock'):
            return

        # Filter the values based on input
        value = event.widget.get()
        if value == '':
            filtered_states = self.us_states
        else:
            filtered_states = [state for state in self.us_states if value.lower() in state.lower()]

        # Show dropdown with filtered results
        self.show_address_dropdown(filtered_states)

    def show_address_dropdown(self, states):
        """Show custom dropdown with filtered states"""
        # Hide existing dropdown
        self.hide_address_dropdown()

        if not states:
            return

        # Get entry position
        x = self.address_entry.winfo_rootx()
        y = self.address_entry.winfo_rooty() + self.address_entry.winfo_height()

        # Create dropdown window
        self.address_dropdown = tk.Toplevel(self.root)
        self.address_dropdown.geometry(f"250x150+{x}+{y}")
        self.address_dropdown.overrideredirect(True)  # Remove window decorations
        self.address_dropdown.attributes("-topmost", True)  # Stay on top

        # Create listbox
        self.address_listbox = tk.Listbox(self.address_dropdown, height=6, width=30,
                                         font=('Segoe UI', 10), selectmode=tk.SINGLE)
        self.address_listbox.pack(fill=tk.BOTH, expand=True)

        # Add states to listbox
        for state in states:
            self.address_listbox.insert(tk.END, state)

        # Bind events
        self.address_listbox.bind('<ButtonRelease-1>', self.on_address_select)
        self.address_listbox.bind('<Return>', self.on_address_select)
        self.address_listbox.bind('<Escape>', self.hide_address_dropdown)

        # Select first item
        if states:
            self.address_listbox.selection_set(0)

        # Bind click outside to close dropdown
        self.root.bind('<Button-1>', self.on_click_outside_dropdown)

    def hide_address_dropdown(self, event=None):
        """Hide the custom dropdown"""
        if self.address_dropdown:
            self.address_dropdown.destroy()
            self.address_dropdown = None
            self.address_listbox = None
            # Unbind the click outside event
            self.root.unbind('<Button-1>')

    def on_click_outside_dropdown(self, event):
        """Handle click outside dropdown to close it"""
        if self.address_dropdown:
            # Get click position
            click_x = event.x_root
            click_y = event.y_root

            # Get dropdown position and size
            dropdown_x = self.address_dropdown.winfo_rootx()
            dropdown_y = self.address_dropdown.winfo_rooty()
            dropdown_width = self.address_dropdown.winfo_width()
            dropdown_height = self.address_dropdown.winfo_height()

            # Check if click is outside dropdown
            if not (dropdown_x <= click_x <= dropdown_x + dropdown_width and
                    dropdown_y <= click_y <= dropdown_y + dropdown_height):
                self.hide_address_dropdown()

    def toggle_address_dropdown(self):
        """Toggle dropdown visibility"""
        if self.address_dropdown:
            self.hide_address_dropdown()
        else:
            value = self.address_entry.get()
            if value == '':
                filtered_states = self.us_states
            else:
                filtered_states = [state for state in self.us_states if value.lower() in state.lower()]
            self.show_address_dropdown(filtered_states)

    def on_address_select(self, event=None):
        """Handle state selection from dropdown"""
        if self.address_listbox and self.address_listbox.curselection():
            selected_index = self.address_listbox.curselection()[0]
            selected_state = self.address_listbox.get(selected_index)
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, selected_state)
        self.hide_address_dropdown()

    def check_hide_dropdown(self):
        """Check if dropdown should be hidden after focus loss"""
        # Only hide if dropdown still exists and entry doesn't have focus
        if self.address_dropdown and not self.address_entry.focus_get():
            self.hide_address_dropdown()

    def on_address_focus_out(self, event):
        """Hide dropdown when focus leaves entry (with delay to allow clicks)"""
        # Don't hide immediately to allow for dropdown clicks
        self.root.after(150, self.check_hide_dropdown)

    def on_iso_focus_in(self, event):
        """Remove placeholder text when ISO entry is focused"""
        if self.iso_entry.get() == "Có thể để trống":
            self.iso_entry.delete(0, tk.END)
            self.iso_entry.config(foreground='black')

    def on_iso_focus_out(self, event):
        """Restore placeholder text if ISO entry is empty"""
        if self.iso_entry.get() == "":
            self.iso_entry.insert(0, "Có thể để trống")
            self.iso_entry.config(foreground='grey')

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
            messagebox.showerror("Error", "Please select an Address!")
            return False

        # Validate sock format (host:port:user:passwd)
        sock_parts = sock.split(":")
        if len(sock_parts) != 4:
            messagebox.showerror("Error", "Sock format should be: host:port:user:passwd")
            return False

        return True

    def start_automation(self):
        if not self.validate_inputs():
            return

        name = self.name_entry.get().strip()
        sock = self.sock_entry.get().strip()
        address = self.address_entry.get().strip()
        iso_path = self.iso_entry.get().strip()

        # Check if iso_path is placeholder text, treat as empty
        if iso_path == "Có thể để trống":
            iso_path = ""

        # Store info and close window (iso_path can be empty)
        self.info = [name, sock, address, iso_path]
        self.root.quit()
        self.root.destroy()

    def browse_iso(self):
        filename = filedialog.askopenfilename(
            title="Select ISO File",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if filename:
            self.iso_entry.delete(0, tk.END)
            self.iso_entry.insert(0, filename)
            self.iso_entry.config(foreground='black')
            self.status_label.config(text="✅ ISO file selected successfully", foreground="#27ae60")
            self.root.after(2000, lambda: self.status_label.config(
                text="💡 Note: Tắt Unikey hoặc chuyển qua tiếng Anh trước khi start", foreground="#7f8c8d"))

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.sock_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.iso_entry.delete(0, tk.END)
        self.iso_entry.insert(0, "Có thể để trống")
        self.iso_entry.config(foreground='grey')
        self.hide_address_dropdown()
        self.status_label.config(text="🗑️ All fields cleared", foreground="#e67e22")
        self.root.after(2000, lambda: self.status_label.config(
            text="💡 Note: Tắt Unikey hoặc chuyển qua tiếng Anh trước khi start", foreground="#7f8c8d"))

def get_vm_info():
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
