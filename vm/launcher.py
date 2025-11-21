import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import random

from states import US_STATES

NOTE = "❌ Chú ý: Không được di chuyển chuột khi tool đang chạy."

DEFAULT_ADDRESSES = [
    "New Orleans, Louisiana",
    "Baton Rouge, Louisiana",
    "Shreveport, Louisiana",
    "Lafayette, Louisiana",
    "Lake Charles, Louisiana",
    "Monroe, Louisiana",
]

class VMAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Autify")
        self.root.geometry("680x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        # Variables to store info
        self.info = None
        self.mode = "full"

        # Table rows data
        self.table_rows = []

        # Row count label
        self.row_count_label = None

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

        # Status label with better styling
        status_frame = ttk.Frame(main_frame, style='Card.TFrame', relief="solid", borderwidth=1)
        status_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(status_frame,
                                     text=NOTE,
                                     font=('Segoe UI', 10, 'bold'),
                                     foreground="white",
                                     background="red",
                                     padding=(10, 5))
        self.status_label.pack(fill=tk.X)

        # ISO Path section
        iso_card_frame = ttk.Frame(main_frame, style='Card.TFrame')
        iso_card_frame.grid(row=1, column=0, columnspan=2, pady=(0, 12), sticky=(tk.W, tk.E))

        iso_frame = ttk.Frame(iso_card_frame)
        iso_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.iso_entry = ttk.Entry(iso_frame, font=('Segoe UI', 10), foreground='grey')
        self.iso_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.iso_entry.insert(0, "Select ISO file path...")
        # Bind events for placeholder behavior
        self.iso_entry.bind('<FocusIn>', self.on_iso_focus_in)
        self.iso_entry.bind('<FocusOut>', self.on_iso_focus_out)
        browse_button = tk.Button(iso_frame, text="� Browse",
                                 command=self.browse_iso,
                                 bg="#3498db", fg="white",
                                 font=('Segoe UI', 9, 'bold'),
                                 width=10,
                                 cursor="hand2",
                                 relief="flat")
        browse_button.grid(row=0, column=1, padx=(10, 0))
        iso_frame.columnconfigure(0, weight=1)
        iso_card_frame.columnconfigure(0, weight=1)

        # Table section
        table_card_frame = ttk.Frame(main_frame, padding="8", style='Card.TFrame',
                                     relief="solid", borderwidth=1)
        table_card_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E, tk.N, tk.S))

        # Buttons section (moved to bottom)
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        # Only VM button
        self.only_vm_button = tk.Button(button_frame, text="💻 Run only VM",
                                        command=self.start_only_vm,
                                        bg="#3498db", fg="white",
                                        font=('Segoe UI', 10, 'bold'),
                                        padx=16, pady=3,
                                        cursor="hand2",
                                        relief="flat",
                                        activebackground="#2980b9",
                                        activeforeground="white")
        self.only_vm_button.grid(row=0, column=0, padx=4)

        # Only Goless button
        # self.only_goless_button = tk.Button(button_frame, text="🤖 Only Goless",
        #                                     command=self.start_only_goless,
        #                                     bg="#9b59b6", fg="white",
        #                                     font=('Segoe UI', 10, 'bold'),
        #                                     padx=16, pady=3,
        #                                     cursor="hand2",
        #                                     relief="flat",
        #                                     activebackground="#8e44ad",
        #                                     activeforeground="white")
        # self.only_goless_button.grid(row=0, column=1, padx=4)

        # Start button
        self.start_button = tk.Button(button_frame, text="▶ Run all",
                                      command=self.start_automation,
                                      bg="#27ae60", fg="white",
                                      font=('Segoe UI', 11, 'bold'),
                                      padx=24, pady=1,
                                      cursor="hand2",
                                      relief="flat",
                                      activebackground="#229954",
                                      activeforeground="white")
        self.start_button.grid(row=0, column=2, padx=4)

        # Table header
        header_frame = ttk.Frame(table_card_frame, style='Card.TFrame')
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Label(header_frame, text="Name", style='Field.TLabel', width=22).grid(row=0, column=0, padx=2)
        ttk.Label(header_frame, text="Sock", style='Field.TLabel', width=35).grid(row=0, column=1, padx=2)
        ttk.Label(header_frame, text="Address", style='Field.TLabel', width=25).grid(row=0, column=2, padx=2)
        self.row_count_label = ttk.Label(header_frame, text="0", width=6, font=('Segoe UI', 9, 'bold'),)
        self.row_count_label.grid(row=0, column=3, padx=2)

        # Table rows container with scrollbar
        table_container = ttk.Frame(table_card_frame, style='Card.TFrame')
        table_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Canvas and scrollbar for table
        self.table_canvas = tk.Canvas(table_container, height=150, bg="white", highlightthickness=0)
        self.table_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.table_canvas.yview)
        self.table_frame = ttk.Frame(self.table_canvas, style='Card.TFrame')

        self.table_canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.table_canvas.configure(yscrollcommand=self.on_canvas_scroll)

        self.table_canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Update scroll region when frame changes
        self.table_frame.bind("<Configure>", self.update_scrollbar)

        # Add more button
        add_button_frame = ttk.Frame(table_card_frame, style='Card.TFrame')
        add_button_frame.grid(row=2, column=0, pady=(10, 0))

        add_more_button = tk.Button(add_button_frame, text="➕ Add more",
                                    command=self.add_table_row,
                                    bg="#16a085", fg="white",
                                    font=('Segoe UI', 9, 'bold'),
                                    padx=12, pady=2,
                                    cursor="hand2",
                                    relief="flat",
                                    activebackground="#138D75",
                                    activeforeground="white")
        add_more_button.pack()

        # Configure table card frame weights
        table_card_frame.columnconfigure(0, weight=1)
        table_card_frame.rowconfigure(1, weight=1)

        # Custom dropdown variables
        self.address_dropdown = None
        self.address_listbox = None

        # Add initial row
        self.add_table_row()

        # Update initial row count
        self.update_row_count()

        # Bind mouse wheel events for scrolling to the entire table area
        table_container.bind("<MouseWheel>", self.on_mouse_wheel)
        table_container.bind("<Button-4>", self.on_mouse_wheel)
        table_container.bind("<Button-5>", self.on_mouse_wheel)

        # Also bind to table frame for complete coverage
        self.table_frame.bind("<MouseWheel>", self.on_mouse_wheel)
        self.table_frame.bind("<Button-4>", self.on_mouse_wheel)
        self.table_frame.bind("<Button-5>", self.on_mouse_wheel)

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def update_scrollbar(self, event=None):
        """Update scroll region and show/hide scrollbar based on content size"""
        self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))

        # Check if content is larger than canvas
        bbox = self.table_canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = self.table_canvas.winfo_height()

            if content_height > canvas_height:
                # Content is larger, show scrollbar
                self.table_scrollbar.pack(side="right", fill="y")
            else:
                # Content fits, hide scrollbar
                self.table_scrollbar.pack_forget()

    def update_row_count(self):
        """Update the row count label"""
        if self.row_count_label:
            self.row_count_label.config(text=str(len(self.table_rows)))

    def on_canvas_scroll(self, *args):
        """Handle canvas scroll and update scrollbar"""
        self.table_scrollbar.set(*args)
        # Update scrollbar visibility when scrolling
        self.root.after(10, self.update_scrollbar)

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling for the table canvas"""
        # For Windows
        if event.delta:
            self.table_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # For Linux/Mac
        elif event.num == 4:
            self.table_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.table_canvas.yview_scroll(1, "units")

    def add_table_row(self, name="", sock="", address=""):
        """Add a new row to the table"""
        row_index = len(self.table_rows)

        row_frame = ttk.Frame(self.table_frame, style='Card.TFrame')
        row_frame.grid(row=row_index, column=0, sticky=(tk.W, tk.E), pady=2)

        # Name entry
        name_entry = ttk.Entry(row_frame, width=22, font=('Segoe UI', 9))
        name_entry.grid(row=0, column=0, padx=2)
        if not name and row_index == 0:
            name = "2022-example.com"
        name_entry.insert(0, name)

        # Sock entry
        sock_entry = ttk.Entry(row_frame, width=35, font=('Segoe UI', 9))
        sock_entry.grid(row=0, column=1, padx=2)
        if not sock and row_index == 0:
            sock = "185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw"
        sock_entry.insert(0, sock)

        # Address frame with entry and dropdown
        address_container = ttk.Frame(row_frame, style='Card.TFrame')
        address_container.grid(row=0, column=2, padx=2)

        address_entry = ttk.Entry(address_container, width=23, font=('Segoe UI', 9))
        address_entry.grid(row=0, column=0)
        if not address:
            address = random.choice(DEFAULT_ADDRESSES)
        address_entry.insert(0, address)

        address_dropdown_btn = tk.Button(address_container, text="▼", width=1,
                                        command=lambda e=address_entry: self.toggle_row_address_dropdown(e),
                                        bg="#f0f0f0", fg="black", font=('Segoe UI', 7),
                                        relief="flat", cursor="hand2")
        address_dropdown_btn.grid(row=0, column=1, padx=(2, 0))

        # Bind mouse wheel to address dropdown button
        address_dropdown_btn.bind('<MouseWheel>', self.on_mouse_wheel)
        address_dropdown_btn.bind('<Button-4>', self.on_mouse_wheel)
        address_dropdown_btn.bind('<Button-5>', self.on_mouse_wheel)

        # Bind autocomplete functionality
        address_entry.bind('<KeyRelease>', lambda event, e=address_entry: self.on_row_address_keyrelease(event, e))
        address_entry.bind('<FocusOut>', self.on_address_focus_out)
        address_entry.bind('<Escape>', self.hide_address_dropdown)

        # Bind mouse wheel to all row widgets for scrolling
        name_entry.bind('<MouseWheel>', self.on_mouse_wheel)
        name_entry.bind('<Button-4>', self.on_mouse_wheel)
        name_entry.bind('<Button-5>', self.on_mouse_wheel)

        sock_entry.bind('<MouseWheel>', self.on_mouse_wheel)
        sock_entry.bind('<Button-4>', self.on_mouse_wheel)
        sock_entry.bind('<Button-5>', self.on_mouse_wheel)

        address_entry.bind('<MouseWheel>', self.on_mouse_wheel)
        address_entry.bind('<Button-4>', self.on_mouse_wheel)
        address_entry.bind('<Button-5>', self.on_mouse_wheel)

        # Delete button
        delete_button = tk.Button(row_frame, text="🗑️",
                                 command=lambda: self.delete_table_row(row_frame, row_data),
                                 bg="white", fg="#e74c3c",
                                 font=('Segoe UI', 12),
                                 cursor="hand2",
                                 relief="flat",
                                 borderwidth=0,
                                 activebackground="white",
                                 activeforeground="#c0392b")
        delete_button.grid(row=0, column=3, padx=(15, 2))

        # Bind mouse wheel to delete button
        delete_button.bind('<MouseWheel>', self.on_mouse_wheel)
        delete_button.bind('<Button-4>', self.on_mouse_wheel)
        delete_button.bind('<Button-5>', self.on_mouse_wheel)

        # Store row data
        row_data = {
            'frame': row_frame,
            'name_entry': name_entry,
            'sock_entry': sock_entry,
            'address_entry': address_entry
        }
        self.table_rows.append(row_data)

        # Update scrollbar visibility after adding
        self.root.after(50, self.update_scrollbar)

        # Update row count
        self.update_row_count()

        return row_data

    def delete_table_row(self, frame, row_data):
        """Delete a row from the table"""
        if len(self.table_rows) <= 1:
            messagebox.showwarning("Warning", "You must have at least one row!")
            return

        # Remove from list
        if row_data in self.table_rows:
            self.table_rows.remove(row_data)

        # Destroy the frame
        frame.destroy()

        # Reindex remaining rows
        for idx, row in enumerate(self.table_rows):
            row['frame'].grid(row=idx, column=0, sticky=(tk.W, tk.E), pady=2)

        # Update scrollbar visibility after deletion
        self.root.after(50, self.update_scrollbar)

        # Update row count
        self.update_row_count()

    def toggle_row_address_dropdown(self, entry_widget):
        """Toggle dropdown visibility for a specific row address entry"""
        if self.address_dropdown:
            self.hide_address_dropdown()
        else:
            value = entry_widget.get()
            if value == '':
                filtered_states = self.us_states
            else:
                filtered_states = [state for state in self.us_states if value.lower() in state.lower()]
            self.show_row_address_dropdown(entry_widget, filtered_states)

    def on_row_address_keyrelease(self, event, entry_widget):
        """Filter address dropdown based on user input for row entry"""
        # Ignore modifier keys
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                            'Caps_Lock', 'Num_Lock', 'Scroll_Lock'):
            return

        # Filter the values based on input
        value = entry_widget.get()
        if value == '':
            filtered_states = self.us_states
        else:
            filtered_states = [state for state in self.us_states if value.lower() in state.lower()]

        # Show dropdown with filtered results
        self.show_row_address_dropdown(entry_widget, filtered_states)

    def show_row_address_dropdown(self, entry_widget, states):
        """Show custom dropdown with filtered states for row entry"""
        # Hide existing dropdown
        self.hide_address_dropdown()

        if not states:
            return

        # Get entry position
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()

        # Create dropdown window
        self.address_dropdown = tk.Toplevel(self.root)
        self.address_dropdown.geometry(f"250x150+{x}+{y}")
        self.address_dropdown.overrideredirect(True)
        self.address_dropdown.attributes("-topmost", True)

        # Create listbox
        self.address_listbox = tk.Listbox(self.address_dropdown, height=6, width=30,
                                         font=('Segoe UI', 10), selectmode=tk.SINGLE)
        self.address_listbox.pack(fill=tk.BOTH, expand=True)

        # Add states to listbox
        for state in states:
            self.address_listbox.insert(tk.END, state)

        # Bind events - pass the entry widget
        self.address_listbox.bind('<ButtonRelease-1>', lambda e, widget=entry_widget: self.on_row_address_select(e, widget))
        self.address_listbox.bind('<Return>', lambda e, widget=entry_widget: self.on_row_address_select(e, widget))
        self.address_listbox.bind('<Escape>', self.hide_address_dropdown)

        # Select first item
        if states:
            self.address_listbox.selection_set(0)

        # Bind click outside to close dropdown
        self.root.bind('<Button-1>', self.on_click_outside_dropdown)

        # Store the current entry widget
        self.current_address_entry = entry_widget

    def on_row_address_select(self, event, entry_widget):
        """Handle state selection from dropdown for row entry"""
        if self.address_listbox and self.address_listbox.curselection():
            selected_index = self.address_listbox.curselection()[0]
            selected_state = self.address_listbox.get(selected_index)
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, selected_state)
        self.hide_address_dropdown()



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
        if self.iso_entry.get() == "Select ISO file path...":
            self.iso_entry.delete(0, tk.END)
            self.iso_entry.config(foreground='black')

    def on_iso_focus_out(self, event):
        """Restore placeholder text if ISO entry is empty"""
        if self.iso_entry.get() == "":
            self.iso_entry.insert(0, "Select ISO file path...")
            self.iso_entry.config(foreground='grey')

    def validate_inputs(self):
        """Validate input fields"""
        if not self.table_rows:
            messagebox.showerror("Error", "Please add at least one row!")
            return False

        for idx, row in enumerate(self.table_rows):
            name = row['name_entry'].get().strip()
            sock = row['sock_entry'].get().strip()
            address = row['address_entry'].get().strip()

            if not name:
                messagebox.showerror("Error", f"Please enter a Name for row {idx + 1}!")
                return False

            if not sock:
                messagebox.showerror("Error", f"Please enter Sock information for row {idx + 1}!")
                return False

            if not address:
                messagebox.showerror("Error", f"Please select an Address for row {idx + 1}!")
                return False

            # Validate sock format (host:port:user:passwd)
            sock_parts = sock.split(":")
            if len(sock_parts) != 4:
                messagebox.showerror("Error", f"Sock format should be: host:port:user:passwd for row {idx + 1}")
                return False

        return True

    def start_automation(self):
        self.mode = "full"
        self._start_process()

    def start_only_vm(self):
        self.mode = "vm"
        self._start_process()

    def start_only_goless(self):
        self.mode = "goless"
        self._start_process()

    def _start_process(self):
        if not self.validate_inputs():
            return

        iso_path = self.iso_entry.get().strip()

        # Check if iso_path is placeholder text, treat as empty
        if iso_path == "Select ISO file path..." or iso_path == "":
            iso_path = ""

        # Collect all rows data
        rows_data = []
        for row in self.table_rows:
            name = row['name_entry'].get().strip()
            sock = row['sock_entry'].get().strip()
            address = row['address_entry'].get().strip()
            rows_data.append([name, sock, address])

        # Store info and close window (iso_path can be empty)
        # Format: [rows_data, iso_path, mode]
        self.info = [rows_data, iso_path, self.mode]
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
            self.status_label.config(text="✅ ISO file selected successfully", background="green")
            self.root.after(1000, lambda: self.status_label.config(text=NOTE, background="red"))

def get_vm_info():
    root = tk.Tk()
    app = VMAutomationGUI(root)
    root.mainloop()
    return app.info

if __name__ == "__main__":
    info = get_vm_info()
    if info:
        rows_data, iso_path, mode = info
        print(f"✓ Mode: {mode}")
        print(f"✓ ISO Path: {iso_path if iso_path else '(auto-detect)'}")
        print(f"✓ Total rows: {len(rows_data)}")
        for idx, row in enumerate(rows_data):
            print(f"\n  Row {idx + 1}:")
            print(f"    Name: {row[0]}")
            print(f"    Sock: {row[1]}")
            print(f"    Address: {row[2]}")
    else:
        print("✗ Cancelled")
