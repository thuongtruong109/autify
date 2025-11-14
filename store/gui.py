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

from utils import load_credentials
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

        # Load credentials on startup
        self.load_credentials_on_start()

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure button styles
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
        """Create all GUI widgets"""
        # Header Frame
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame,
                              text="🛍️ Store Automation Tool",
                              font=('Segoe UI', 20, 'bold'),
                              bg='#2c3e50',
                              fg='white')
        title_label.pack(pady=20)

        # Main Container
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Credentials Info Frame
        info_frame = tk.LabelFrame(main_container,
                                   text="📌 Store Information",
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   padx=10,
                                   pady=10)
        info_frame.pack(fill='x', pady=(0, 15))

        self.store_label = tk.Label(info_frame,
                                    text="Store: Not loaded",
                                    font=('Segoe UI', 10),
                                    bg='#ecf0f1',
                                    fg='#34495e',
                                    anchor='w')
        self.store_label.pack(fill='x', pady=2)

        self.email_label = tk.Label(info_frame,
                                    text="Email: Not loaded",
                                    font=('Segoe UI', 10),
                                    bg='#ecf0f1',
                                    fg='#34495e',
                                    anchor='w')
        self.email_label.pack(fill='x', pady=2)

        self.status_label = tk.Label(info_frame,
                                     text="Status: ⚪ Not logged in",
                                     font=('Segoe UI', 10, 'bold'),
                                     bg='#ecf0f1',
                                     fg='#e74c3c',
                                     anchor='w')
        self.status_label.pack(fill='x', pady=2)

        # Login Button
        self.login_button = ttk.Button(info_frame,
                                      text="🔐 Login to Shopify",
                                      style='Login.TButton',
                                      command=self.login_action)
        self.login_button.pack(pady=10)

        # Tasks Frame
        tasks_frame = tk.LabelFrame(main_container,
                                   text="🎯 Available Tasks",
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   padx=15,
                                   pady=10)
        tasks_frame.pack(fill='both', expand=True, pady=(0, 15))

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

        # Log Frame
        log_frame = tk.LabelFrame(main_container,
                                 text="📋 Activity Log",
                                 font=('Segoe UI', 11, 'bold'),
                                 bg='#ecf0f1',
                                 fg='#2c3e50',
                                 padx=10,
                                 pady=10)
        log_frame.pack(fill='both', expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=8,
                                                 font=('Consolas', 9),
                                                 bg='#2c3e50',
                                                 fg='#ecf0f1',
                                                 insertbackground='white',
                                                 wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)

        # Redirect stdout to log
        sys.stdout = TextRedirector(self.log_text, "stdout")

        self.log("Application started successfully")

    def load_credentials_on_start(self):
        """Load credentials when app starts"""
        try:
            self.credentials = load_credentials()
            if self.credentials:
                email = self.credentials.get('email', 'N/A')
                store_id = self.credentials.get('storeId', 'N/A')

                self.store_label.config(text=f"Store: {store_id}")
                self.email_label.config(text=f"Email: {email}")
                self.log(f"✅ Credentials loaded for store: {store_id}")
            else:
                self.log("⚠️ No credentials found in config.json")
                messagebox.showwarning("Warning", "No credentials found. Please check config.json file.")
        except Exception as e:
            self.log(f"❌ Error loading credentials: {e}")
            messagebox.showerror("Error", f"Failed to load credentials: {e}")

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

        if not self.credentials:
            messagebox.showerror("Error", "No credentials loaded. Please check config.json file.")
            return

        # Disable login button
        self.login_button.config(state='disabled')

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
                self.root.after(0, lambda: self.login_button.config(state='normal'))

                if self.driver:
                    self.driver.quit()
                    self.driver = None

        except Exception as e:
            self.log(f"❌ Login error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Login error:\n{e}"))
            self.root.after(0, lambda: self.login_button.config(state='normal'))

            if self.driver:
                self.driver.quit()
                self.driver = None

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

            # Check if task requires policies
            if task_func == setup_legal_policies:
                policies = self.credentials.get('policies', {})
                task_func(self.driver, store_id, policies)
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
