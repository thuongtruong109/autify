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

from auth import login_to_shopify, start_captcha_monitor, stop_captcha_monitor
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
        self.root.geometry("600x700")
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
                       padding=[20, 5],
                       font=('Segoe UI', 11, 'bold'),
                       background='#bdc3c7',
                       foreground='#2c3e50',
                       width=15)  # Fixed width to prevent size change
        style.map('TNotebook.Tab',
                 background=[('selected', '#3498db'), ('active', '#5dade2')],
                 foreground=[('selected', 'white'), ('active', 'white')],
                 padding=[('selected', [20, 5]), ('active', [20, 5])])  # Keep same padding        # Configure button styles
        style.configure('Task.TButton',
                       padding=5,
                       font=('Segoe UI', 10),
                       background='#4CAF50',
                       foreground='white')

        style.map('Task.TButton',
                 background=[('active', '#45a049'), ('disabled', '#cccccc')])

        style.configure('Login.TButton',
                       padding=5,
                       font=('Segoe UI', 11, 'bold'),
                       background='#2196F3',
                       foreground='white')

        style.map('Login.TButton',
                 background=[('active', '#1976D2'), ('disabled', '#cccccc')])

    def setup_placeholder(self, entry, placeholder_text):
        """Setup placeholder behavior for Entry widget"""
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(fg='#2c3e50')  # Normal text color

        def on_focus_out(event):
            if entry.get() == '':
                entry.insert(0, placeholder_text)
                entry.config(fg='#95a5a6')  # Placeholder color

        # Set initial placeholder
        entry.insert(0, placeholder_text)
        entry.config(fg='#95a5a6')  # Placeholder color

        # Bind events
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def setup_text_placeholder(self, text_widget, placeholder_text):
        """Setup placeholder behavior for ScrolledText widget"""
        def on_focus_in(event):
            current_text = text_widget.get('1.0', tk.END).strip()
            if current_text == placeholder_text:
                text_widget.delete('1.0', tk.END)
                text_widget.config(fg='#2c3e50')  # Normal text color

        def on_focus_out(event):
            current_text = text_widget.get('1.0', tk.END).strip()
            if current_text == '':
                text_widget.insert('1.0', placeholder_text)
                text_widget.config(fg='#95a5a6')  # Placeholder color

        # Set initial placeholder
        text_widget.insert('1.0', placeholder_text)
        text_widget.config(fg='#95a5a6')  # Placeholder color

        # Bind events
        text_widget.bind('<FocusIn>', on_focus_in)
        text_widget.bind('<FocusOut>', on_focus_out)

    def create_widgets(self):

        # Main Container
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill='both', expand=True, padx=6, pady=6)

        # Create Notebook (Tabs)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)

        # Login frame (placed on top-right of notebook)
        login_frame = tk.Frame(main_container, bg='#ecf0f1')
        login_frame.place(relx=1.0, rely=0, anchor='ne', height=40)

        # Status icon (initially not logged in)
        self.status_icon = tk.Label(login_frame, text="⚪", font=('Segoe UI', 12), bg='#2196F3', fg='white')
        self.status_icon.pack()

        # Login Button
        self.login_button = tk.Button(login_frame,
                                      text="🔐 Login",
                                      font=('Segoe UI', 11, 'bold'),
                                      bg='#2196F3',
                                      fg='white',
                                      command=self.login_action,
                                      relief='raised',
                                      bd=0,
                                      padx=20,
                                      pady=3,
                                      activebackground='#1976D2',
                                      activeforeground='white')
        self.login_button.pack()

        # Place status icon absolutely on the button
        self.status_icon.place(in_=self.login_button, relx=0.85, rely=0.5, anchor='center')

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
                                 padx=6,
                                 pady=6)
        log_frame.pack(fill='both', expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=4,
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

        # Pack scrollable_frame into canvas with full width
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw', width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # Update scrollable_frame width when canvas resizes
        def update_scrollable_width(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)

        canvas.bind('<Configure>', update_scrollable_width)

        # Enable mousewheel scrolling with smart handling for textareas
        def _on_mousewheel(event):
            """Smart mousewheel handler that scrolls canvas when textarea can't scroll"""
            widget = event.widget

            # Check if widget is a ScrolledText
            if isinstance(widget, scrolledtext.ScrolledText):
                # Get current scroll position
                try:
                    yview = widget.yview()
                    scroll_direction = -1 if event.delta > 0 else 1

                    # If scrolling up and already at top, scroll canvas
                    if scroll_direction == -1 and yview[0] <= 0:
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                        return "break"
                    # If scrolling down and already at bottom, scroll canvas
                    elif scroll_direction == 1 and yview[1] >= 1:
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                        return "break"
                    # Otherwise, let the textarea handle its own scrolling
                    else:
                        return
                except:
                    pass

            # For all other widgets, scroll the canvas
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def bind_mousewheel_recursive(widget, callback):
            """Recursively bind mousewheel to widget and all its children"""
            widget.bind("<MouseWheel>", callback)
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child, callback)

        # Bind mousewheel to canvas, tab_frame and all children
        canvas.bind("<MouseWheel>", _on_mousewheel)
        tab_frame.bind("<MouseWheel>", _on_mousewheel)

        # Update bindings whenever scrollable_frame is configured
        def update_bindings(event=None):
            bind_mousewheel_recursive(scrollable_frame, _on_mousewheel)

        scrollable_frame.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            update_bindings()
        ))

        # Initial binding
        update_bindings()

        # Credentials Input Frame
        input_frame = tk.LabelFrame(scrollable_frame,
                                    text="🔑 Store Credentials",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#ecf0f1',
                                    fg='#2c3e50',
                                    pady=10,
                                    borderwidth=0)
        input_frame.pack(fill='both', expand=True, pady=(10, 15))

        # Email - using placeholder instead of label
        self.email_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=60)
        self.email_entry.grid(row=1, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.email_entry, 'Email address')

        # Password - using placeholder instead of label
        self.password_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=60, show='*')
        self.password_entry.grid(row=2, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.password_entry, 'Password')

        # Configure grid
        input_frame.columnconfigure(0, weight=1)

        # SEO Frame
        seo_frame = tk.LabelFrame(scrollable_frame,
                      text="⚙️ Preferences",
                      font=('Segoe UI', 11, 'bold'),
                      bg='#ecf0f1',
                      fg='#2c3e50',
                      pady=10,
                      borderwidth=0)
        seo_frame.pack(fill='both', expand=True, pady=(0, 15))

        # SEO Title - using placeholder instead of label
        self.seo_title_entry = tk.Entry(seo_frame, font=('Segoe UI', 10), width=60)
        self.seo_title_entry.grid(row=0, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.seo_title_entry, 'SEO title')

        # SEO Description - using placeholder instead of label
        self.seo_description_entry = tk.Entry(seo_frame, font=('Segoe UI', 10), width=60)
        self.seo_description_entry.grid(row=1, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.seo_description_entry, 'SEO description')

        # Configure grid
        seo_frame.columnconfigure(0, weight=1)

        # Pages Frame
        pages_frame = tk.LabelFrame(scrollable_frame,
                        text="📄 Policies",
                        font=('Segoe UI', 11, 'bold'),
                        bg='#ecf0f1',
                        fg='#2c3e50',
                        pady=10,
                        borderwidth=0)
        pages_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Return & Refund Policy - using placeholder instead of label
        self.return_refund_text = scrolledtext.ScrolledText(pages_frame, height=4, font=('Segoe UI', 9), wrap=tk.WORD)
        self.return_refund_text.grid(row=0, column=0, sticky='ew', pady=5)
        self.setup_text_placeholder(self.return_refund_text, 'Return and refund policy...')

        # Terms of Service - using placeholder instead of label
        self.terms_service_text = scrolledtext.ScrolledText(pages_frame, height=4, font=('Segoe UI', 9), wrap=tk.WORD)
        self.terms_service_text.grid(row=1, column=0, sticky='ew', pady=5)
        self.setup_text_placeholder(self.terms_service_text, 'Terms of service...')

        # Shipping Policy - using placeholder instead of label
        self.shipping_policy_text = scrolledtext.ScrolledText(pages_frame, height=4, font=('Segoe UI', 9), wrap=tk.WORD)
        self.shipping_policy_text.grid(row=2, column=0, sticky='ew', pady=5)
        self.setup_text_placeholder(self.shipping_policy_text, 'Shipping policy...')

        # Contact Information - using placeholder instead of label
        self.contact_info_text = scrolledtext.ScrolledText(pages_frame, height=4, font=('Segoe UI', 9), wrap=tk.WORD)
        self.contact_info_text.grid(row=3, column=0, sticky='ew', pady=5)
        self.setup_text_placeholder(self.contact_info_text, 'Contact information...')

        # Configure grid
        pages_frame.columnconfigure(0, weight=1)

        # Marketing Frame
        marketing_frame = tk.LabelFrame(scrollable_frame,
                           text="📢 Marketing",
                           font=('Segoe UI', 11, 'bold'),
                           bg='#ecf0f1',
                           fg='#2c3e50',
                           pady=10,
                           borderwidth=0)
        marketing_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Marketing Subject - using placeholder instead of label
        self.marketing_subject_entry = tk.Entry(marketing_frame, font=('Segoe UI', 10), width=60)
        self.marketing_subject_entry.grid(row=0, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.marketing_subject_entry, 'Marketing subject line')

        # Configure grid
        marketing_frame.columnconfigure(0, weight=1)

        # Upsell Frame
        upsell_frame = tk.LabelFrame(scrollable_frame,
                        text="💰 Upsell",
                        font=('Segoe UI', 11, 'bold'),
                        bg='#ecf0f1',
                        fg='#2c3e50',
                        pady=10,
                        borderwidth=0)
        upsell_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Upsell Campaign Title - using placeholder instead of label
        self.upsell_campaign_title_entry = tk.Entry(upsell_frame, font=('Segoe UI', 10), width=60)
        self.upsell_campaign_title_entry.grid(row=0, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.upsell_campaign_title_entry, 'Upsell campaign title')

        # Upsell Thank You - using placeholder instead of label
        self.upsell_thank_you_entry = tk.Entry(upsell_frame, font=('Segoe UI', 10), width=60)
        self.upsell_thank_you_entry.grid(row=1, column=0, sticky='ew', pady=5)
        self.setup_placeholder(self.upsell_thank_you_entry, 'Upsell thank you message')

        # Configure grid
        upsell_frame.columnconfigure(0, weight=1)

        # Pages Frame
        pages_content_frame = tk.LabelFrame(scrollable_frame,
                        text="📄 Pages",
                        font=('Segoe UI', 11, 'bold'),
                        bg='#ecf0f1',
                        fg='#2c3e50',
                        pady=10,
                        borderwidth=0)
        pages_content_frame.pack(fill='both', expand=True, pady=(0, 15))

        # About Us - using placeholder instead of label
        self.about_us_text = scrolledtext.ScrolledText(pages_content_frame, height=4, font=('Segoe UI', 9), wrap=tk.WORD)
        self.about_us_text.grid(row=0, column=0, sticky='ew', pady=5)
        self.setup_text_placeholder(self.about_us_text, 'About Us page content...')

        # Contact Us - using placeholder instead of label
        self.contact_us_text = scrolledtext.ScrolledText(pages_content_frame, height=4, font=('Segoe UI', 9), wrap=tk.WORD)
        self.contact_us_text.grid(row=1, column=0, sticky='ew', pady=5)
        self.setup_text_placeholder(self.contact_us_text, 'Contact Us page content...')

        # Configure grid
        pages_content_frame.columnconfigure(0, weight=1)

        # Image with Text Frame (3 rows; each row has Title + Description side-by-side)
        image_text_frame = tk.LabelFrame(scrollable_frame,
                        text="🖼️ Image with Text",
                        font=('Segoe UI', 11, 'bold'),
                        bg='#ecf0f1',
                        fg='#2c3e50',
                        pady=10,
                        borderwidth=0)
        image_text_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Column headers
        tk.Label(image_text_frame, text="Title", font=('Segoe UI', 10, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=0, sticky='w', padx=(2, 8))
        tk.Label(image_text_frame, text="Description", font=('Segoe UI', 10, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=1, sticky='w', padx=(8, 2))

        # Row 1
        self.image_text_title_1_entry = tk.Entry(image_text_frame, font=('Segoe UI', 10))
        self.image_text_title_1_entry.grid(row=1, column=0, sticky='ew', pady=4, padx=(0, 8))
        self.image_text_desc_1_entry = tk.Entry(image_text_frame, font=('Segoe UI', 10))
        self.image_text_desc_1_entry.grid(row=1, column=1, sticky='ew', pady=4, padx=(8, 0))

        # Row 2
        self.image_text_title_2_entry = tk.Entry(image_text_frame, font=('Segoe UI', 10))
        self.image_text_title_2_entry.grid(row=2, column=0, sticky='ew', pady=4, padx=(0, 8))
        self.image_text_desc_2_entry = tk.Entry(image_text_frame, font=('Segoe UI', 10))
        self.image_text_desc_2_entry.grid(row=2, column=1, sticky='ew', pady=4, padx=(8, 0))

        # Row 3
        self.image_text_title_3_entry = tk.Entry(image_text_frame, font=('Segoe UI', 10))
        self.image_text_title_3_entry.grid(row=3, column=0, sticky='ew', pady=4, padx=(0, 8))
        self.image_text_desc_3_entry = tk.Entry(image_text_frame, font=('Segoe UI', 10))
        self.image_text_desc_3_entry.grid(row=3, column=1, sticky='ew', pady=4, padx=(8, 0))

        # Configure grid for equal column expansion
        image_text_frame.columnconfigure(0, weight=1)
        image_text_frame.columnconfigure(1, weight=1)

        # Slider Frame (3 rows; each row has Name + YouTube Short Link side-by-side)
        slider_frame = tk.LabelFrame(scrollable_frame,
                        text="🎠 Slider",
                        font=('Segoe UI', 11, 'bold'),
                        bg='#ecf0f1',
                        fg='#2c3e50',
                        pady=10,
                        borderwidth=0)
        slider_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Column headers
        tk.Label(slider_frame, text="Name", font=('Segoe UI', 10, 'bold'),
            bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=0, sticky='w', padx=(2, 8))
        tk.Label(slider_frame, text="YouTube Short Link", font=('Segoe UI', 10, 'bold'),
            bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=1, sticky='w', padx=(8, 2))

        # Row 1
        self.slider_name_1_entry = tk.Entry(slider_frame, font=('Segoe UI', 10))
        self.slider_name_1_entry.grid(row=1, column=0, sticky='ew', pady=4, padx=(0, 8))
        self.slider_link_1_entry = tk.Entry(slider_frame, font=('Segoe UI', 10))
        self.slider_link_1_entry.grid(row=1, column=1, sticky='ew', pady=4, padx=(8, 0))

        # Row 2
        self.slider_name_2_entry = tk.Entry(slider_frame, font=('Segoe UI', 10))
        self.slider_name_2_entry.grid(row=2, column=0, sticky='ew', pady=4, padx=(0, 8))
        self.slider_link_2_entry = tk.Entry(slider_frame, font=('Segoe UI', 10))
        self.slider_link_2_entry.grid(row=2, column=1, sticky='ew', pady=4, padx=(8, 0))

        # Row 3
        self.slider_name_3_entry = tk.Entry(slider_frame, font=('Segoe UI', 10))
        self.slider_name_3_entry.grid(row=3, column=0, sticky='ew', pady=4, padx=(0, 8))
        self.slider_link_3_entry = tk.Entry(slider_frame, font=('Segoe UI', 10))
        self.slider_link_3_entry.grid(row=3, column=1, sticky='ew', pady=4, padx=(8, 0))

        # Configure grid for equal column expansion
        slider_frame.columnconfigure(0, weight=1)
        slider_frame.columnconfigure(1, weight=1)

        # Product Section: 4 products, each with name (input), description (textarea), and two prices on same row
        product_section = tk.LabelFrame(scrollable_frame,
                        text="🛍️ Products",
                        font=('Segoe UI', 11, 'bold'),
                        bg='#ecf0f1',
                        fg='#2c3e50',
                        pady=10,
                        borderwidth=0)
        product_section.pack(fill='both', expand=True, pady=(0, 15))

        for i in range(1, 5):
            # container for each product
            item_frame = tk.Frame(product_section, bg='#ecf0f1')
            item_frame.pack(fill='x', expand=True, pady=(8, 8))
            item_frame.columnconfigure(0, weight=1)

            # Product name (row 1)
            tk.Label(item_frame, text=f"Product {i} Name:", font=('Segoe UI', 10), bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=0, sticky='w')
            setattr(self, f'product_{i}_name_entry', tk.Entry(item_frame, font=('Segoe UI', 10)))
            getattr(self, f'product_{i}_name_entry').grid(row=1, column=0, sticky='ew', pady=4)
            self.setup_placeholder(getattr(self, f'product_{i}_name_entry'), f'Product {i} Name')

            # Product description (row 2) - using placeholder instead of label
            setattr(self, f'product_{i}_desc_text', scrolledtext.ScrolledText(item_frame, height=3, font=('Segoe UI', 9), wrap=tk.WORD))
            getattr(self, f'product_{i}_desc_text').grid(row=2, column=0, sticky='ew', pady=4)
            self.setup_text_placeholder(getattr(self, f'product_{i}_desc_text'), f'Description for Product {i}...')

            # Price row (row 3) - discount and original side-by-side
            price_frame = tk.Frame(item_frame, bg='#ecf0f1')
            price_frame.grid(row=3, column=0, sticky='ew', pady=4)
            price_frame.columnconfigure(0, weight=1)
            price_frame.columnconfigure(1, weight=1)

            tk.Label(price_frame, text='Discount Price', font=('Segoe UI', 10), bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=0, sticky='w')
            tk.Label(price_frame, text='Original Price', font=('Segoe UI', 10), bg='#ecf0f1', fg='#2c3e50').grid(row=0, column=1, sticky='w')

            setattr(self, f'product_{i}_discount_entry', tk.Entry(price_frame, font=('Segoe UI', 10)))
            getattr(self, f'product_{i}_discount_entry').grid(row=1, column=0, sticky='ew', padx=(0, 6))
            self.setup_placeholder(getattr(self, f'product_{i}_discount_entry'), '0.00')
            setattr(self, f'product_{i}_original_entry', tk.Entry(price_frame, font=('Segoe UI', 10)))
            getattr(self, f'product_{i}_original_entry').grid(row=1, column=1, sticky='ew', padx=(6, 0))
            self.setup_placeholder(getattr(self, f'product_{i}_original_entry'), '0.00')

            # Add divider between products (except after the last one)
            if i < 4:
                divider = tk.Frame(product_section, bg='#bdc3c7', height=1)
                divider.pack(fill='x', pady=(5, 10))

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

        # Pack scrollable_frame into canvas with full width
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw', width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # Update scrollable_frame width when canvas resizes
        def update_scrollable_width(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)

        canvas.bind('<Configure>', update_scrollable_width)

        # Enable mousewheel scrolling with smart handling for textareas
        def _on_mousewheel(event):
            """Smart mousewheel handler that scrolls canvas when textarea can't scroll"""
            widget = event.widget

            # Check if widget is a ScrolledText
            if isinstance(widget, scrolledtext.ScrolledText):
                # Get current scroll position
                try:
                    yview = widget.yview()
                    scroll_direction = -1 if event.delta > 0 else 1

                    # If scrolling up and already at top, scroll canvas
                    if scroll_direction == -1 and yview[0] <= 0:
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                        return "break"
                    # If scrolling down and already at bottom, scroll canvas
                    elif scroll_direction == 1 and yview[1] >= 1:
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                        return "break"
                    # Otherwise, let the textarea handle its own scrolling
                    else:
                        return
                except:
                    pass

            # For all other widgets, scroll the canvas
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def bind_mousewheel_recursive(widget, callback):
            """Recursively bind mousewheel to widget and all its children"""
            widget.bind("<MouseWheel>", callback)
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child, callback)

        # Bind mousewheel to canvas, tab_frame and all children
        canvas.bind("<MouseWheel>", _on_mousewheel)
        tab_frame.bind("<MouseWheel>", _on_mousewheel)

        # Update bindings whenever scrollable_frame is configured
        def update_bindings(event=None):
            bind_mousewheel_recursive(scrollable_frame, _on_mousewheel)

        scrollable_frame.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            update_bindings()
        ))

        # Initial binding
        update_bindings()

        # Tasks Frame
        tasks_frame = tk.LabelFrame(scrollable_frame,
                                   text="🎯 Available Tasks",
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   padx=15,
                                   pady=10)
        tasks_frame.pack(fill='both', expand=True, pady=(10, 10))

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
            },
            'marketing': {
                'subject': self.marketing_subject_entry.get().strip()
            },
            'upsell': {
                'campaign_title': self.upsell_campaign_title_entry.get().strip(),
                'thank_you': self.upsell_thank_you_entry.get().strip()
            },
            'image_text': {
                'titles': [
                    self.image_text_title_1_entry.get().strip(),
                    self.image_text_title_2_entry.get().strip(),
                    self.image_text_title_3_entry.get().strip()
                ],
                'descriptions': [
                    self.image_text_desc_1_entry.get().strip(),
                    self.image_text_desc_2_entry.get().strip(),
                    self.image_text_desc_3_entry.get().strip()
                ]
            },
            'slider': {
                'names': [
                    self.slider_name_1_entry.get().strip(),
                    self.slider_name_2_entry.get().strip(),
                    self.slider_name_3_entry.get().strip()
                ],
                'youtube_links': [
                    self.slider_link_1_entry.get().strip(),
                    self.slider_link_2_entry.get().strip(),
                    self.slider_link_3_entry.get().strip()
                ]
            }
            ,
            'products': [
                {
                    'name': getattr(self, f'product_{i}_name_entry').get().strip(),
                    'description': getattr(self, f'product_{i}_desc_text').get('1.0', tk.END).strip(),
                    'discount_price': getattr(self, f'product_{i}_discount_entry').get().strip(),
                    'original_price': getattr(self, f'product_{i}_original_entry').get().strip()
                } for i in range(1, 5)
            ]
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

            # Khởi động captcha monitor ngay sau khi setup driver
            self.log("🔄 Starting Cloudflare captcha auto-monitor...")
            start_captcha_monitor(driver, check_interval=2.0)

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
                self.root.after(0, lambda: self.status_icon.config(text="❌", fg='#e74c3c'))

                if self.driver:
                    stop_captcha_monitor()
                    self.driver.quit()
                    self.driver = None

        except Exception as e:
            self.log(f"❌ Login error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Login error:\n{e}"))
            self.root.after(0, self.enable_inputs)
            self.root.after(0, lambda: self.status_icon.config(text="❌", fg='#e74c3c'))

            if self.driver:
                stop_captcha_monitor()
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
        self.status_icon.config(text="⚪", fg='white')

    def on_login_success(self):
        """Update UI after successful login"""
        self.status_icon.config(text="✅", fg='#27ae60')
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
            elif task_func == handle_dser_open_and_confirm:
                password = self.credentials.get('password', '')
                task_func(self.driver, store_id, password)
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
                    # Dừng captcha monitor trước khi đóng browser
                    stop_captcha_monitor()
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
        # Also write to terminal
        sys.__stdout__.write(text)
        sys.__stdout__.flush()

    def flush(self):
        sys.__stdout__.flush()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = StoreAutomationGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
