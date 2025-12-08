import sys
import os

if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from auth import login_to_shopify, register_shopify_account, start_captcha_monitor, stop_captcha_monitor
from install import install_apps
from store.dsers.import_product import handle_dser_open_and_confirm
from market import setup_world_market
from policies import setup_legal_policies
from pages import setup_contact_page
from shipping import setup_shipping_zones
from preference import setup_preferences
from domain import connect_domain
from selleasy import setup_selleasy
from content import setup_content_menus

class StoreAutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autify")
        self.setGeometry(100, 100, 600, 700)
        self.setFixedSize(600, 700)
        self.setWindowIcon(QIcon(os.path.join(base_path, 'favicon.ico')))

        # Variables
        self.driver = None
        self.is_logged_in = False
        self.credentials = None

        # Setup UI
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        """Configure Qt stylesheets"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
                border: none;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 20px;
                font: bold 11px 'Segoe UI';
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton#loginButton {
                background-color: #2196F3;
                font: bold 11px 'Segoe UI';
                padding: 6px 20px;
                border-radius: 6px;
            }
            QPushButton#loginButton:hover {
                background-color: #1976D2;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font: 10px 'Segoe UI';
                background-color: white;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font: 11px 'Consolas';
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QTextEdit#inputText, QTextEdit#productText {
                background-color: white;
                color: #2c3e50;
                font: 10px 'Segoe UI';
            }
            QGroupBox {
                font: bold 11px 'Segoe UI';
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #2c3e50;
                font: 10px 'Segoe UI';
            }
            QScrollArea {
                border: none;
            }
        """)


    def create_widgets(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)

        # Create tab widget
        self.notebook = QTabWidget()
        self.notebook.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #ecf0f1;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                color: #2c3e50;
                padding: 6px 16px;
                margin-right: 4px;
                font: bold 11px 'Segoe UI';
                min-width: 80px;
                border: 1px solid #dee2e6;
                border-radius: 6px 6px 0 0;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #e3f2fd);
                color: #007bff;

            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #e3f2fd);
                color: #1976d2;
            }
        """)
        main_layout.addWidget(self.notebook)

        # Login frame (now in the same row as tabs)
        login_frame = QWidget()
        login_layout = QHBoxLayout(login_frame)
        login_layout.setContentsMargins(0, 0, 0, 0)

        # Status icon
        self.status_icon = QLabel("⚪")
        self.status_icon.setStyleSheet("font-size: 12px; color: white; background-color: #2196F3; border-radius: 50%; text-align: center; padding: 0;")
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setFixedSize(20, 20)
        login_layout.addWidget(self.status_icon)

        # Login Button
        self.login_button = QPushButton("🔐 Login")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.login_action)
        login_layout.addWidget(self.login_button)

        # Set login frame as corner widget in the tab bar
        self.notebook.setCornerWidget(login_frame)

        # Create Credentials Tab
        self.credentials_tab = self.create_credentials_tab()
        self.notebook.addTab(self.credentials_tab, '🔑 Credentials')

        # Create Tasks Tab
        self.tasks_tab = self.create_tasks_tab()
        self.notebook.addTab(self.tasks_tab, '🎯 Tasks')

        # Log Frame (at bottom)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(80)  # Reduce entire section height by half
        main_layout.addWidget(self.log_text)

        # Redirect stdout to log
        sys.stdout = TextRedirector(self.log_text, "stdout")

        self.log("Application started successfully")
        self.log("Please enter your store credentials and click Login")

    def create_credentials_tab(self):
        """Create the Credentials tab with scroll area"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create container widget for scroll area
        container = QWidget()
        scroll_area.setWidget(container)

        # Main layout for container
        layout = QVBoxLayout(container)

        # Credentials Input Frame
        credentical_group = QGroupBox("🔑 Credentials")
        layout.addWidget(credentical_group)

        credentical_layout = QVBoxLayout(credentical_group)
        credentical_layout.setSpacing(3)
        credentical_layout.setContentsMargins(4, 2, 4, 4)

        # Store ID
        self.store_id_entry = QLineEdit()
        self.store_id_entry.setPlaceholderText('Domain')
        credentical_layout.addWidget(self.store_id_entry)

        # Email
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText('Email address')
        credentical_layout.addWidget(self.email_entry)

        # Password
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setPlaceholderText('Password')
        credentical_layout.addWidget(self.password_entry)

        # SEO Frame
        seo_group = QGroupBox("⚙️ Preferences")
        layout.addWidget(seo_group)

        seo_layout = QVBoxLayout(seo_group)
        seo_layout.setSpacing(3)
        seo_layout.setContentsMargins(4, 2, 4, 4)

        # SEO Title
        self.seo_title_entry = QLineEdit()
        self.seo_title_entry.setPlaceholderText('SEO title')
        seo_layout.addWidget(self.seo_title_entry)

        # SEO Description
        self.seo_description_entry = QLineEdit()
        self.seo_description_entry.setPlaceholderText('SEO description')
        seo_layout.addWidget(self.seo_description_entry)

        # Pages Frame
        pages_group = QGroupBox("📄 Policies")
        layout.addWidget(pages_group)

        pages_layout = QVBoxLayout(pages_group)
        pages_layout.setSpacing(3)
        pages_layout.setContentsMargins(4, 2, 4, 4)

        # Return & Refund Policy
        self.return_refund_text = QTextEdit()
        self.return_refund_text.setObjectName("inputText")
        self.return_refund_text.setPlaceholderText('Return and refund policy...')
        self.return_refund_text.setMaximumHeight(80)
        pages_layout.addWidget(self.return_refund_text)

        # Terms of Service
        self.terms_service_text = QTextEdit()
        self.terms_service_text.setObjectName("inputText")
        self.terms_service_text.setPlaceholderText('Terms of service...')
        self.terms_service_text.setMaximumHeight(80)
        pages_layout.addWidget(self.terms_service_text)

        # Shipping Policy
        self.shipping_policy_text = QTextEdit()
        self.shipping_policy_text.setObjectName("inputText")
        self.shipping_policy_text.setPlaceholderText('Shipping policy...')
        self.shipping_policy_text.setMaximumHeight(80)
        pages_layout.addWidget(self.shipping_policy_text)

        # Contact Information
        self.contact_info_text = QTextEdit()
        self.contact_info_text.setObjectName("inputText")
        self.contact_info_text.setPlaceholderText('Contact information...')
        self.contact_info_text.setMaximumHeight(80)
        pages_layout.addWidget(self.contact_info_text)

        # Marketing Frame
        marketing_group = QGroupBox("📢 Marketing")
        layout.addWidget(marketing_group)

        marketing_layout = QVBoxLayout(marketing_group)
        marketing_layout.setContentsMargins(4, 2, 4, 4)

        # Marketing Subject
        self.marketing_subject_entry = QLineEdit()
        self.marketing_subject_entry.setPlaceholderText('Marketing subject line')
        marketing_layout.addWidget(self.marketing_subject_entry)

        # Upsell Frame
        upsell_group = QGroupBox("💰 Upsell")
        layout.addWidget(upsell_group)

        upsell_layout = QVBoxLayout(upsell_group)
        upsell_layout.setSpacing(3)
        upsell_layout.setContentsMargins(4, 2, 4, 4)

        # Upsell Campaign Title
        self.upsell_campaign_title_entry = QLineEdit()
        self.upsell_campaign_title_entry.setPlaceholderText('Upsell campaign title')
        upsell_layout.addWidget(self.upsell_campaign_title_entry)

        # Upsell Thank You
        self.upsell_thank_you_entry = QLineEdit()
        self.upsell_thank_you_entry.setPlaceholderText('Upsell thank you message')
        upsell_layout.addWidget(self.upsell_thank_you_entry)

        # Pages Content Frame
        pages_content_group = QGroupBox("📄 Pages")
        layout.addWidget(pages_content_group)

        pages_content_layout = QVBoxLayout(pages_content_group)
        pages_content_layout.setSpacing(3)
        pages_content_layout.setContentsMargins(4, 2, 4, 4)

        # About Us
        self.about_us_text = QTextEdit()
        self.about_us_text.setObjectName("inputText")
        self.about_us_text.setPlaceholderText('About Us page content...')
        self.about_us_text.setMaximumHeight(80)
        pages_content_layout.addWidget(self.about_us_text)

        # Contact Us
        self.contact_us_text = QTextEdit()
        self.contact_us_text.setObjectName("inputText")
        self.contact_us_text.setPlaceholderText('Contact Us page content...')
        self.contact_us_text.setMaximumHeight(80)
        pages_content_layout.addWidget(self.contact_us_text)

        # Product Section
        product_group = QGroupBox("🛍️ Products")
        layout.addWidget(product_group)

        product_layout = QVBoxLayout(product_group)
        product_layout.setContentsMargins(2, 2, 2, 2)

        discount_values = [49.99, 79.99, 99.99, 119.99]
        original_values = [99, 119, 149, 179]
        for i, v in enumerate(discount_values, start=1):
            product_widget = QWidget()
            product_layout.addWidget(product_widget)

            product_item_layout = QVBoxLayout(product_widget)
            product_item_layout.setSpacing(3)
            product_item_layout.setContentsMargins(2, 2, 2, 2)

            # Product name
            setattr(self, f'product_{i}_name_entry', QLineEdit())
            getattr(self, f'product_{i}_name_entry').setPlaceholderText(f'Product {i} name')
            product_item_layout.addWidget(getattr(self, f'product_{i}_name_entry'))

            # Product description
            desc_layout = QHBoxLayout()
            setattr(self, f'product_{i}_desc_text', QTextEdit())
            getattr(self, f'product_{i}_desc_text').setObjectName("productText")
            getattr(self, f'product_{i}_desc_text').setMaximumHeight(60)
            getattr(self, f'product_{i}_desc_text').setPlaceholderText(f'Product {i} description...')
            product_item_layout.addWidget(getattr(self, f'product_{i}_desc_text'))

            # Price row
            price_layout = QHBoxLayout()
            setattr(self, f'product_{i}_discount_entry', QLineEdit())
            getattr(self, f'product_{i}_discount_entry').setText(str(v))
            getattr(self, f'product_{i}_discount_entry').setPlaceholderText('Discount price')
            price_layout.addWidget(getattr(self, f'product_{i}_discount_entry'))

            setattr(self, f'product_{i}_original_entry', QLineEdit())
            getattr(self, f'product_{i}_original_entry').setText(str(original_values[i-1]))
            getattr(self, f'product_{i}_original_entry').setPlaceholderText('Original price')
            price_layout.addWidget(getattr(self, f'product_{i}_original_entry'))

            product_item_layout.addLayout(price_layout)

            # Add separator
            if i < 4:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("QFrame { border: none; border-top: 1px dashed #959797; }")
                product_layout.addWidget(separator)

        # Image with Text Frame
        image_text_group = QGroupBox("🖼️ Image with Text")
        layout.addWidget(image_text_group)

        image_text_layout = QVBoxLayout(image_text_group)
        image_text_layout.setContentsMargins(2, 2, 2, 2)

        iwt_plhd = [
            {
                "title":  "Home title",
                "desc": "Home description"
            },
            {
                "title":  "Product title 1",
                "desc": "Product description 1"
            },
            {
                "title":  "Product title 2",
                "desc": "Product description 2"
            }
        ]

        for i, v in enumerate(iwt_plhd, start=1):
            image_text_widget = QWidget()
            image_text_layout.addWidget(image_text_widget)

            image_text_item_layout = QVBoxLayout(image_text_widget)
            image_text_item_layout.setSpacing(3)
            image_text_item_layout.setContentsMargins(2, 2, 2, 2)

            # Title
            setattr(self, f'image_text_title_{i}_entry', QLineEdit())
            getattr(self, f'image_text_title_{i}_entry').setPlaceholderText(f"{v['title']}")
            image_text_item_layout.addWidget(getattr(self, f'image_text_title_{i}_entry'))

            # Description
            setattr(self, f'image_text_desc_{i}_entry', QTextEdit())
            getattr(self, f'image_text_desc_{i}_entry').setObjectName("productText")
            getattr(self, f'image_text_desc_{i}_entry').setMaximumHeight(60)
            getattr(self, f'image_text_desc_{i}_entry').setPlaceholderText(f"{v['desc']}")
            image_text_item_layout.addWidget(getattr(self, f'image_text_desc_{i}_entry'))

            # Add separator
            if i < 3:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("QFrame { border: none; border-top: 1px dashed #959797; }")
                image_text_layout.addWidget(separator)

        # Slider Frame
        slider_group = QGroupBox("🎠 Slider")
        layout.addWidget(slider_group)

        slider_layout = QGridLayout(slider_group)
        slider_layout.setSpacing(3)
        slider_layout.setContentsMargins(4, 2, 4, 4)

        slider_layout.setColumnStretch(0, 1)
        slider_layout.setColumnStretch(1, 3)

        # Row 1
        self.slider_name_1_entry = QLineEdit()
        self.slider_name_1_entry.setPlaceholderText("Name 1")
        slider_layout.addWidget(self.slider_name_1_entry, 0, 0)
        self.slider_link_1_entry = QLineEdit()
        self.slider_link_1_entry.setPlaceholderText("Short video link 1")
        slider_layout.addWidget(self.slider_link_1_entry, 0, 1)

        # Row 2
        self.slider_name_2_entry = QLineEdit()
        self.slider_name_2_entry.setPlaceholderText("Name 2")
        slider_layout.addWidget(self.slider_name_2_entry, 1, 0)
        self.slider_link_2_entry = QLineEdit()
        self.slider_link_2_entry.setPlaceholderText("Short video link 2")
        slider_layout.addWidget(self.slider_link_2_entry, 1, 1)

        # Row 3
        self.slider_name_3_entry = QLineEdit()
        self.slider_name_3_entry.setPlaceholderText("Name 3")
        slider_layout.addWidget(self.slider_name_3_entry, 2, 0)
        self.slider_link_3_entry = QLineEdit()
        self.slider_link_3_entry.setPlaceholderText("Short video link 3")
        slider_layout.addWidget(self.slider_link_3_entry, 2, 1)

        # Reviews Section
        reviews_group = QGroupBox("📝 Reviews")
        layout.addWidget(reviews_group)

        reviews_layout = QVBoxLayout(reviews_group)
        reviews_layout.setContentsMargins(2, 2, 2, 2)
        reviews_layout.setSpacing(0)

        for i in range(1, 11):
            review_widget = QWidget()
            reviews_layout.addWidget(review_widget)

            review_item_layout = QVBoxLayout(review_widget)
            review_item_layout.setSpacing(0)
            review_item_layout.setContentsMargins(2, 2, 2, 2)

            file_layout = QHBoxLayout()
            file_layout.setSpacing(3)
            setattr(self, f'review_file_{i}_name_entry', QLineEdit())
            getattr(self, f'review_file_{i}_name_entry').setPlaceholderText(f'Review text {i}')
            file_layout.addWidget(getattr(self, f'review_file_{i}_name_entry'))
            setattr(self, f'review_file_{i}_browse_button', QPushButton('Browse'))
            getattr(self, f'review_file_{i}_browse_button').clicked.connect(lambda checked, idx=i: self.browse_review_file(idx))
            file_layout.addWidget(getattr(self, f'review_file_{i}_browse_button'))

            review_item_layout.addLayout(file_layout)

        # FAQ Section
        faq_group = QGroupBox("❓ FAQ")
        layout.addWidget(faq_group)

        faq_layout = QVBoxLayout(faq_group)
        faq_layout.setContentsMargins(2, 2, 2, 2)

        for i in range(1, 7):
            faq_widget = QWidget()
            faq_layout.addWidget(faq_widget)

            faq_item_layout = QVBoxLayout(faq_widget)
            faq_item_layout.setSpacing(3)
            faq_item_layout.setContentsMargins(2, 2, 2, 2)

            # FAQ question
            setattr(self, f'faq_{i}_question_entry', QLineEdit())
            getattr(self, f'faq_{i}_question_entry').setPlaceholderText(f'FAQ question {i}')
            faq_item_layout.addWidget(getattr(self, f'faq_{i}_question_entry'))

            # FAQ answer
            setattr(self, f'faq_{i}_answer_text', QTextEdit())
            getattr(self, f'faq_{i}_answer_text').setObjectName("productText")
            getattr(self, f'faq_{i}_answer_text').setMaximumHeight(60)
            getattr(self, f'faq_{i}_answer_text').setPlaceholderText(f'FAQ answer {i}...')
            faq_item_layout.addWidget(getattr(self, f'faq_{i}_answer_text'))

            # Add separator
            if i < 6:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("QFrame { border: none; border-top: 1px dashed #959797; }")
                faq_layout.addWidget(separator)

        layout.addStretch()

        return scroll_area

    def create_tasks_tab(self):
        """Create the Tasks tab"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create container widget
        container = QWidget()
        scroll_area.setWidget(container)

        # Main layout
        layout = QVBoxLayout(container)

        # Tasks Frame
        tasks_group = QGroupBox("🎯 Available Tasks")
        layout.addWidget(tasks_group)

        tasks_layout = QGridLayout(tasks_group)
        tasks_layout.setSpacing(3)
        tasks_layout.setContentsMargins(4, 2, 4, 4)

        # Create task buttons
        self.task_buttons = {}
        tasks = [
            ('register_shopify_account', '🆕 Register', register_shopify_account),
            ('install_apps', '📦 Install Apps', install_apps),
            ('handle_dser_open_and_confirm', '🛠️ DSers (progress)', handle_dser_open_and_confirm),
            ('setup_world_market', '🌍 Markets', setup_world_market),
            ('setup_legal_policies', '📜 Policies', setup_legal_policies),
            ('setup_contact_page', '📄 Pages', setup_contact_page),
            ('setup_shipping_zones', '🚚 Shipping', setup_shipping_zones),
            ('setup_preferences', '⚙️ Preferences', setup_preferences),
            ('connect_domain', '🌐 Connect Domain', connect_domain),
            ('setup_selleasy', '🎯 Selleasy', setup_selleasy),
            ('setup_content_menus', '📋 Content Menus', setup_content_menus),
        ]

        row = 0
        col = 0
        for task_id, task_label, task_func in tasks:
            btn = QPushButton(task_label)
            btn.setEnabled(False)
            btn.clicked.connect(lambda checked, f=task_func, l=task_label: self.run_task(f, l))
            tasks_layout.addWidget(btn, row, col)
            self.task_buttons[task_id] = btn

            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1

        # Add stretch
        layout.addStretch()

        return scroll_area

    def validate_inputs(self):
        """Validate input fields"""
        store_id = self.store_id_entry.text().strip()
        email = self.email_entry.text().strip()
        password = self.password_entry.text()
        seo_title = self.seo_title_entry.text().strip()
        seo_description = self.seo_description_entry.text().strip()

        if not store_id:
            QMessageBox.critical(self, "Error", "Domain is required!")
            return False
        if not email:
            QMessageBox.critical(self, "Error", "Email is required!")
            return False
        if not password:
            QMessageBox.critical(self, "Error", "Password is required!")
            return False
        if not seo_title:
            QMessageBox.critical(self, "Error", "SEO Title is required!")
            return False
        if not seo_description:
            QMessageBox.critical(self, "Error", "SEO Description is required!")
            return False

        return True

    def get_credentials_from_inputs(self):
        """Get credentials from input fields"""
        return {
            'storeId': self.store_id_entry.text().strip(),
            'email': self.email_entry.text().strip(),
            'password': self.password_entry.text(),
            'seo': {
                'title': self.seo_title_entry.text().strip(),
                'description': self.seo_description_entry.text().strip()
            },
            'marketing': {
                'subject': self.marketing_subject_entry.text().strip()
            },
            'upsell': {
                'campaign_title': self.upsell_campaign_title_entry.text().strip(),
                'thank_you': self.upsell_thank_you_entry.text().strip()
            },
            'image_text': {
                'titles': [
                    self.image_text_title_1_entry.text().strip(),
                    self.image_text_title_2_entry.text().strip(),
                    self.image_text_title_3_entry.text().strip()
                ],
                'descriptions': [
                    self.image_text_desc_1_entry.toPlainText().strip(),
                    self.image_text_desc_2_entry.toPlainText().strip(),
                    self.image_text_desc_3_entry.toPlainText().strip()
                ]
            },
            'slider': {
                'names': [
                    self.slider_name_1_entry.text().strip(),
                    self.slider_name_2_entry.text().strip(),
                    self.slider_name_3_entry.text().strip()
                ],
                'youtube_links': [
                    self.slider_link_1_entry.text().strip(),
                    self.slider_link_2_entry.text().strip(),
                    self.slider_link_3_entry.text().strip()
                ]
            },
            'products': [
                {
                    'name': getattr(self, f'product_{i}_name_entry').text().strip(),
                    'description': getattr(self, f'product_{i}_desc_text').toPlainText().strip(),
                    'discount_price': getattr(self, f'product_{i}_discount_entry').text().strip(),
                    'original_price': getattr(self, f'product_{i}_original_entry').text().strip()
                } for i in range(1, 5)
            ]
        }

    def log(self, message):
        """Add message to log"""
        self.log_text.append(f"{message}")
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

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
            QMessageBox.critical(self, "Error", f"Failed to initialize WebDriver:\n{e}")
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
        self.login_button.setEnabled(False)
        self.store_id_entry.setEnabled(False)
        self.email_entry.setEnabled(False)
        self.password_entry.setEnabled(False)
        self.seo_title_entry.setEnabled(False)
        self.seo_description_entry.setEnabled(False)

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
                QTimer.singleShot(0, self.on_login_success)
            else:
                self.log("❌ Login failed")
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Login Failed", "Could not login to Shopify"))
                QTimer.singleShot(0, self.enable_inputs)
                QTimer.singleShot(0, lambda: self.status_icon.setText("❌"))

                if self.driver:
                    stop_captcha_monitor()
                    self.driver.quit()
                    self.driver = None

        except Exception as e:
            self.log(f"❌ Login error: {e}")
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Login error:\n{e}"))
            QTimer.singleShot(0, self.enable_inputs)
            QTimer.singleShot(0, lambda: self.status_icon.setText("❌"))

            if self.driver:
                stop_captcha_monitor()
                self.driver.quit()
                self.driver = None

    def enable_inputs(self):
        """Re-enable input fields and login button"""
        self.login_button.setEnabled(True)
        self.store_id_entry.setEnabled(True)
        self.email_entry.setEnabled(True)
        self.password_entry.setEnabled(True)
        self.seo_title_entry.setEnabled(True)
        self.seo_description_entry.setEnabled(True)
        self.status_icon.setText("⚪")
        self.status_icon.setStyleSheet("color: white; background-color: #2196F3;")

    def on_login_success(self):
        """Update UI after successful login"""
        self.status_icon.setText("✅")
        self.status_icon.setStyleSheet("color: #27ae60; background-color: #2196F3;")
        self.login_button.setText("✅ Logged In")
        self.login_button.setEnabled(False)

        # Enable all task buttons
        for btn in self.task_buttons.values():
            btn.setEnabled(True)

        QMessageBox.information(self, "Success", "Login successful! You can now run tasks.")

    def run_task(self, task_func, task_label):
        """Run a specific task"""
        if not self.is_logged_in:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return

        # Disable all task buttons during execution
        for btn in self.task_buttons.values():
            btn.setEnabled(False)

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
            elif task_func == register_shopify_account:
                email = self.credentials.get('email', '')
                password = self.credentials.get('password', '')
                task_func(self.driver, email, password, store_id)
            elif task_func == connect_domain:
                task_func(self.driver, store_id, store_id)
            else:
                task_func(self.driver, store_id)

            self.log(f"✅ Task completed: {task_label}")
            self.log(f"{'='*60}\n")

            QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", f"Task completed:\n{task_label}"))

        except Exception as e:
            self.log(f"❌ Error in task {task_label}: {e}")
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Task failed:\n{task_label}\n\nError: {e}"))
        finally:
            # Re-enable all task buttons
            QTimer.singleShot(0, self.enable_task_buttons)

    def enable_task_buttons(self):
        """Re-enable all task buttons"""
        for btn in self.task_buttons.values():
            btn.setEnabled(True)

    def shorten_filename(self, filename, max_length=20):
        """Shorten filename if too long"""
        if len(filename) <= max_length:
            return filename
        else:
            return filename[:7] + "..." + filename[-7:]

    def browse_review_file(self, idx):
        """Browse for reviews file"""
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select Review File {idx}", "", "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.tiff)")
        if file_path:
            # Store the selected file path
            setattr(self, f'review_file_{idx}_path', file_path)
            # Update button text to show file is selected
            button = getattr(self, f'review_file_{idx}_browse_button')
            button.setText(f"Selected: {self.shorten_filename(os.path.basename(file_path))}")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.driver:
            reply = QMessageBox.question(self, "Quit", "Do you want to close the browser and exit?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    # Dừng captcha monitor trước khi đóng browser
                    stop_captcha_monitor()
                    self.driver.quit()
                    self.log("Browser closed")
                except:
                    pass
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class TextRedirector:
    """Redirect stdout/stderr to a QTextEdit widget"""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, text):
        self.widget.append(text.rstrip())
        # Scroll to bottom
        scrollbar = self.widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # Also write to terminal
        sys.__stdout__.write(text)
        sys.__stdout__.flush()

    def flush(self):
        sys.__stdout__.flush()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = StoreAutomationGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
