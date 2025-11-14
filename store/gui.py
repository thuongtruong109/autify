import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

from auth import login_to_shopify
from install import install_apps
from dsers import handle_dser_open_and_confirm
from market import setup_world_market
from policies import setup_legal_policies
from pages import setup_contact_page
from shipping import setup_shipping_zones
from themes import setup_preferences


class StoreAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛍️ Autify")
        self.root.geometry("900x700")
        self.root.resizable(False, False)

        # Variables
        self.driver = None
        self.is_logged_in = False
        self.credentials = None

        # Style
        self.setup_styles()

        # GUI Components
        self.create_widgets()

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure Notebook (Tabs) style
        style.configure('TNotebook', background='#ecf0f1', borderwidth=0)
        style.configure('TNotebook.Tab',
                       padding=[20, 10],
                       font=('Segoe UI', 11, 'bold'),
                       background='#bdc3c7',
                       foreground='#2c3e50',
                       width=15)  # Fixed width to prevent size change
        style.map('TNotebook.Tab',
                 background=[('selected', '#3498db'), ('active', '#5dade2')],
                 foreground=[('selected', 'white'), ('active', 'white')],
                 padding=[('selected', [20, 10]), ('active', [20, 10])])  # Keep same padding        # Configure button styles
        style.configure('Task.TButton',
                       padding=10,
                       font=('Segoe UI', 10),
                       background='#4CAF50',
                       foreground='white')

        style.map('Task.TButton',
                 background=[('active', '#45a049'), ('disabled', '#cccccc')])

        style.configure('Login.TButton',
                       padding=10,
                       font=('Segoe UI', 11, 'bold'),
                       background='#2196F3',
                       foreground='white')

        style.map('Login.TButton',
                 background=[('active', '#1976D2'), ('disabled', '#cccccc')])

    def create_widgets(self):
        # Header Frame
        # header_frame = tk.Frame(self.root, bg='#2c3e50', height=40)
        # header_frame.pack(fill='x')
        # header_frame.pack_propagate(False)

        # title_label = tk.Label(header_frame,
        #                       text="🛍️ Store Automation Tool",
        #                       font=('Segoe UI', 20, 'bold'),
        #                       bg='#2c3e50',
        #                       fg='white')
        # title_label.pack(pady=10)

        # Main Container
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill='both', expand=True, padx=6, pady=6)

        # Create Notebook (Tabs)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)

        # Create Credentials Tab
        self.credentials_tab = self.create_credentials_tab()
        self.notebook.add(self.credentials_tab, text='🔑 Credentials')

        # Create Tasks Tab
        self.tasks_tab = self.create_tasks_tab()
        self.notebook.add(self.tasks_tab, text='🎯 Tasks')

        # Log Frame (outside tabs, at bottom)
        log_frame = tk.LabelFrame(main_container,
                                 text="📋 Activity Log",
                                 font=('Segoe UI', 11, 'bold'),
                                 bg='#ecf0f1',
                                 fg='#2c3e50',
                                 padx=10,
                                 pady=10)
        log_frame.pack(fill='both', expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=6,
                                                 font=('Consolas', 9),
                                                 bg='#2c3e50',
                                                 fg='#ecf0f1',
                                                 insertbackground='white',
                                                 wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)

        # Redirect stdout to log
        sys.stdout = TextRedirector(self.log_text, "stdout")

        self.log("Application started successfully")
        self.log("Please enter your store credentials and click Login")

    def create_credentials_tab(self):
        """Create the Credentials tab with scrollbar"""
        # Create frame for tab
        tab_frame = tk.Frame(self.notebook, bg='#ecf0f1')

        # Create canvas and scrollbar
        canvas = tk.Canvas(tab_frame, bg='#ecf0f1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient='vertical', command=canvas.yview)

        # Create scrollable frame
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Credentials Input Frame
        input_frame = tk.LabelFrame(scrollable_frame,
                                    text="🔑 Store Credentials",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#ecf0f1',
                                    fg='#2c3e50',
                                    padx=15,
                                    pady=10)
        input_frame.pack(fill='x', pady=(10, 15), padx=10)

        # Store ID
        tk.Label(input_frame, text="Store ID:", font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', anchor='w').grid(row=0, column=0, sticky='w', pady=5)
        self.store_id_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=40)
        self.store_id_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))

        # Email
        tk.Label(input_frame, text="Email:", font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', anchor='w').grid(row=1, column=0, sticky='w', pady=5)
        self.email_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=40)
        self.email_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))

        # Password
        tk.Label(input_frame, text="Password:", font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', anchor='w').grid(row=2, column=0, sticky='w', pady=5)
        self.password_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=40, show='*')
        self.password_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))

        # SEO Title
        tk.Label(input_frame, text="SEO Title:", font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', anchor='w').grid(row=3, column=0, sticky='w', pady=5)
        self.seo_title_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=40)
        self.seo_title_entry.grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))

        # SEO Description
        tk.Label(input_frame, text="SEO Description:", font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', anchor='w').grid(row=4, column=0, sticky='w', pady=5)
        self.seo_description_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=40)
        self.seo_description_entry.grid(row=4, column=1, sticky='ew', pady=5, padx=(10, 0))

        # Configure grid
        input_frame.columnconfigure(1, weight=1)

        return tab_frame

    def create_tasks_tab(self):
        """Create the Tasks tab with scrollbar"""
        # Create frame for tab
        tab_frame = tk.Frame(self.notebook, bg='#ecf0f1')

        # Create canvas and scrollbar
        canvas = tk.Canvas(tab_frame, bg='#ecf0f1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient='vertical', command=canvas.yview)

        # Create scrollable frame
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Status Frame
        status_frame = tk.LabelFrame(scrollable_frame,
                                     text="📌 Login Status",
                                     font=('Segoe UI', 11, 'bold'),
                                     bg='#ecf0f1',
                                     fg='#2c3e50',
                                     padx=10,
                                     pady=10)
        status_frame.pack(fill='x', pady=(10, 15), padx=10)

        self.status_label = tk.Label(status_frame,
                                     text="Status: ⚪ Not logged in",
                                     font=('Segoe UI', 10, 'bold'),
                                     bg='#ecf0f1',
                                     fg='#e74c3c',
                                     anchor='w')
        self.status_label.pack(fill='x', pady=2)

        # Login Button
        self.login_button = ttk.Button(status_frame,
                                      text="🔐 Login to Shopify",
                                      style='Login.TButton',
                                      command=self.login_action)
        self.login_button.pack(pady=10)

        # Tasks Frame
        tasks_frame = tk.LabelFrame(scrollable_frame,
                                   text="🎯 Available Tasks",
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   padx=15,
                                   pady=10)
        tasks_frame.pack(fill='both', expand=True, pady=(0, 10), padx=10)

        # Create task buttons in a grid
        self.task_buttons = {}
        tasks = [
            ('install_apps', '📦 Install Apps', install_apps),
            ('handle_dser', '🛠️ DSers (progress)', handle_dser_open_and_confirm),
            ('setup_world_market', '🌍 Markets', setup_world_market),
            ('setup_policies', '📜 Policies', setup_legal_policies),
            ('setup_pages', '📄 Pages', setup_contact_page),
            ('setup_shipping', '🚚 Shipping (progress)', setup_shipping_zones),
            ('setup_preferences', '⚙️ Preferences', setup_preferences),
        ]

        row = 0
        col = 0
        for task_id, task_label, task_func in tasks:
            btn = ttk.Button(tasks_frame,
                           text=task_label,
                           style='Task.TButton',
                           state='disabled',
                           command=lambda f=task_func, l=task_label: self.run_task(f, l))
            btn.grid(row=row, column=col, padx=8, pady=8, sticky='ew')
            self.task_buttons[task_id] = btn

            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1

        # Configure grid columns to expand equally
        tasks_frame.columnconfigure(0, weight=1)
        tasks_frame.columnconfigure(1, weight=1)

        return tab_frame

    def validate_inputs(self):
        """Validate input fields"""
        store_id = self.store_id_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        seo_title = self.seo_title_entry.get().strip()
        seo_description = self.seo_description_entry.get().strip()

        if not store_id:
            messagebox.showerror("Error", "Store ID is required!")
            return False
        if not email:
            messagebox.showerror("Error", "Email is required!")
            return False
        if not password:
            messagebox.showerror("Error", "Password is required!")
            return False
        if not seo_title:
            messagebox.showerror("Error", "SEO Title is required!")
            return False
        if not seo_description:
            messagebox.showerror("Error", "SEO Description is required!")
            return False

        return True

    def get_credentials_from_inputs(self):
        """Get credentials from input fields"""
        return {
            'storeId': self.store_id_entry.get().strip(),
            'email': self.email_entry.get().strip(),
            'password': self.password_entry.get().strip(),
            'seo': {
                'title': self.seo_title_entry.get().strip(),
                'description': self.seo_description_entry.get().strip()
            }
        }

    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()

    def setup_driver(self) -> Optional[webdriver.Chrome]:
        """Setup Chrome WebDriver"""
        try:
            self.log("Setting up Chrome WebDriver...")
            service = Service(ChromeDriverManager().install())

            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")

            user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selenium_data")
            options.add_argument(f"--user-data-dir={user_data_dir}")

            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            options.add_argument("--disable-blink-features=AutomationControlled")

            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(10)

            self.log("✅ WebDriver setup completed")
            return driver
        except Exception as e:
            self.log(f"❌ Critical error initializing WebDriver: {e}")
            messagebox.showerror("Error", f"Failed to initialize WebDriver:\n{e}")
            return None

    def login_action(self):
        """Handle login button click"""
        if self.is_logged_in:
            self.log("⚠️ Already logged in")
            return

        # Validate inputs
        if not self.validate_inputs():
            return

        # Get credentials from input fields
        self.credentials = self.get_credentials_from_inputs()

        self.log(f"📝 Credentials validated for store: {self.credentials['storeId']}")

        # Disable login button and input fields
        self.login_button.config(state='disabled')
        self.store_id_entry.config(state='disabled')
        self.email_entry.config(state='disabled')
        self.password_entry.config(state='disabled')
        self.seo_title_entry.config(state='disabled')
        self.seo_description_entry.config(state='disabled')

        # Run login in separate thread
        thread = threading.Thread(target=self.login_thread, daemon=True)
        thread.start()

    def login_thread(self):
        """Login thread function"""
        try:
            email = self.credentials['email']
            password = self.credentials['password']
            store_id = self.credentials['storeId']

            self.log(f"🔐 Starting login for {email}...")

            self.driver = self.setup_driver()
            if not self.driver:
                self.root.after(0, lambda: self.login_button.config(state='normal'))
                return

            self.log("Attempting to login to Shopify...")
            logged = login_to_shopify(self.driver, email, password, store_id)

            if logged:
                self.is_logged_in = True
                self.log("✅ Login successful!")

                # Update UI in main thread
                self.root.after(0, self.on_login_success)
            else:
                self.log("❌ Login failed")
                self.root.after(0, lambda: messagebox.showerror("Login Failed", "Could not login to Shopify"))
                self.root.after(0, self.enable_inputs)

                if self.driver:
                    self.driver.quit()
                    self.driver = None

        except Exception as e:
            self.log(f"❌ Login error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Login error:\n{e}"))
            self.root.after(0, self.enable_inputs)

            if self.driver:
                self.driver.quit()
                self.driver = None

    def enable_inputs(self):
        """Re-enable input fields and login button"""
        self.login_button.config(state='normal')
        self.store_id_entry.config(state='normal')
        self.email_entry.config(state='normal')
        self.password_entry.config(state='normal')
        self.seo_title_entry.config(state='normal')
        self.seo_description_entry.config(state='normal')

    def on_login_success(self):
        """Update UI after successful login"""
        self.status_label.config(text="Status: 🟢 Logged in", fg='#27ae60')
        self.login_button.config(text="✅ Logged In", state='disabled')

        # Enable all task buttons
        for btn in self.task_buttons.values():
            btn.config(state='normal')

        messagebox.showinfo("Success", "Login successful! You can now run tasks.")

    def run_task(self, task_func, task_label):
        """Run a specific task"""
        if not self.is_logged_in:
            messagebox.showwarning("Warning", "Please login first!")
            return

        # Disable all task buttons during execution
        for btn in self.task_buttons.values():
            btn.config(state='disabled')

        # Run task in separate thread
        thread = threading.Thread(target=self.task_thread, args=(task_func, task_label), daemon=True)
        thread.start()

    def task_thread(self, task_func, task_label):
        """Task execution thread"""
        try:
            self.log(f"\n{'='*60}")
            self.log(f"🚀 Starting task: {task_label}")
            self.log(f"{'='*60}")

            store_id = self.credentials['storeId']

            # Check if task requires special parameters
            if task_func == setup_legal_policies:
                policies = self.credentials.get('policies', {})
                task_func(self.driver, store_id, policies)
            elif task_func == setup_preferences:
                seo_data = self.credentials.get('seo', {})
                task_func(self.driver, store_id, seo_data)
            else:
                task_func(self.driver, store_id)

            self.log(f"✅ Task completed: {task_label}")
            self.log(f"{'='*60}\n")

            self.root.after(0, lambda: messagebox.showinfo("Success", f"Task completed:\n{task_label}"))

        except Exception as e:
            self.log(f"❌ Error in task {task_label}: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Task failed:\n{task_label}\n\nError: {e}"))
        finally:
            # Re-enable all task buttons
            self.root.after(0, self.enable_task_buttons)

    def enable_task_buttons(self):
        """Re-enable all task buttons"""
        for btn in self.task_buttons.values():
            btn.config(state='normal')

    def on_closing(self):
        """Handle window close event"""
        if self.driver:
            if messagebox.askokcancel("Quit", "Do you want to close the browser and exit?"):
                try:
                    self.driver.quit()
                    self.log("Browser closed")
                except:
                    pass
                self.root.destroy()
        else:
            self.root.destroy()


class TextRedirector:
    """Redirect stdout/stderr to a text widget"""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
        self.widget.update()

    def flush(self):
        pass


def main():
    """Main entry point"""
    root = tk.Tk()
    app = StoreAutomationGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
