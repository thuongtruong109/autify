import sys
import os
import re
import asyncio
import traceback

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

from configs.driver import setup_driver
from configs.anti_freeze import AntiFreeze
from auth import login_to_shopify, register_shopify_account, start_captcha_monitor, stop_captcha_monitor
from install import install_apps
from dsers.link_account import link_dser_account
from market import setup_world_market
from policies import setup_legal_policies
from pages import setup_contact_page
from shipping import setup_shipping_zones
from preference import setup_preferences
from domain import connect_domain
from selleasy import setup_selleasy
from content import setup_content_menus
from themes.import_theme import import_theme
from notification import setup_notifications
from configs.app import get_config_json

class ClickableGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.parent = parent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            title_rect = self.titleRect()
            if title_rect.contains(event.position().toPoint()):
                self.parent.toggle_credentials()
                return
        super().mousePressEvent(event)

    def titleRect(self):
        fm = QFontMetrics(self.font())
        title_width = fm.horizontalAdvance(self.title()) + 20
        title_height = fm.height() + 4
        return QRect(10, 2, title_width, title_height)

class PlainTextEdit(QTextEdit):
    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)

class StoreAutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autify")
        self.resize(600, 700)
        self.setFixedSize(600, 700)
        self.setWindowIcon(QIcon(os.path.join(base_path, 'favicon.ico')))

        self.driver = None
        self.heartbeat = None
        self.is_logged_in = False
        self.store_id = None
        self.credentials = None
        self.is_info_sheet = True
        self.is_toggling_card = False
        self.is_toggling_name = False
        self.is_toggling_account = False
        self.is_toggling_info = False
        self.selected_tasks = set()  # Track selected tasks (using set)
        self.task_order = []  # Track original task order
        self.seo_file_path = None

        self.setup_styles()
        self.create_widgets()
        self.card_text.textChanged.connect(self.toggle_card_inputs)
        self.card_number.textChanged.connect(self.toggle_card_inputs)
        self.expired.textChanged.connect(self.toggle_card_inputs)
        self.cvc.textChanged.connect(self.toggle_card_inputs)
        self.name_entry.textChanged.connect(self.toggle_name_inputs)
        self.first_name_entry.textChanged.connect(self.toggle_name_inputs)
        self.last_name_entry.textChanged.connect(self.toggle_name_inputs)
        self.account_text.textChanged.connect(self.toggle_account_inputs)
        self.hotmail_id_entry.textChanged.connect(self.toggle_account_inputs)
        self.hotmail_password_entry.textChanged.connect(self.toggle_account_inputs)
        self.shopify_password_entry.textChanged.connect(self.toggle_account_inputs)
        self.domain_entry.textChanged.connect(self.toggle_account_inputs)
        self.info_text.textChanged.connect(self.toggle_info_inputs)
        self.ssn_entry.textChanged.connect(self.toggle_info_inputs)
        self.birthday_entry.textChanged.connect(self.toggle_info_inputs)
        self.address_entry.textChanged.connect(self.toggle_info_inputs)
        self.zip_entry.textChanged.connect(self.toggle_info_inputs)

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
            QTextEdit#inputText, QTextEdit#productText, QTextEdit#hotmailText, QTextEdit#infoText {
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
            QGroupBox::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #bdc3c7;
                border-radius: 2px;
                background-color: transparent;
            }
            QGroupBox::indicator:checked {
                background-color: #4CAF50;
            }
            QCheckBox {
                spacing: 5px;
                font: 10px 'Segoe UI';
                color: #2c3e50;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #2196F3;
            }
            QCheckBox::indicator:pressed {
                background-color: #45a049;
            }
            QLabel {
                color: #2c3e50;
                font: 10px 'Segoe UI';
            }
            QScrollArea {
                border: none;
            }
        """)


    def extract_generic_patterns(self, text: str):
        pattern = re.compile(
            r"""
            (?P<number>(?:\D*\d{4}){4})
            .*?
            (?P<expired>\d{2}/\d{2})
            .*?
            (?P<cvc>\d{3})
            """,
            re.VERBOSE | re.DOTALL
        )

        match = pattern.search(text)
        if not match:
            return {
                "number": None,
                "expired": None,
                "cvc": None,
            }

        raw_blocks = match.group("number")
        blocks_cleaned = re.findall(r"\d{4}", raw_blocks)
        blocks_joined = "".join(blocks_cleaned) if len(blocks_cleaned) == 4 else None

        return {
            "number": blocks_joined,
            "expired": match.group("expired"),
            "cvc": match.group("cvc"),
        }


    def split_name(self, full_name: str):
        parts = full_name.strip().split()

        if len(parts) < 2:
            return {"first_name": parts[0], "last_name": ""}

        last_name = parts[-1]
        first_name = " ".join(parts[:-1])

        return {"first_name": first_name, "last_name": last_name}

    def parse_account_string(self, text: str):
        parts = re.split(r"[\/|]", text.strip())
        if len(parts) != 3:
            raise ValueError("Chuỗi không đúng định dạng 3 phần ngăn cách bởi '/'")

        hotmail_id = parts[0]
        hotmail_password = parts[1]
        shopify_password = parts[2]

        if "@" in shopify_password:
            domain = shopify_password.split("@")[0]
        else:
            domain = None

        return {
            "hotmail_id": hotmail_id,
            "hotmail_password": hotmail_password,
            "shopify_password": shopify_password,
            "domain": domain
        }

    def extract_info(self, text: str):
        clean = " ".join(text.split())
        pattern = re.compile(
            r"""
            (?P<ssn>\d{9})\s+
            (?P<birthday>\d{1,2}/\d{1,2}/\d{4})
            (?:\s+\d{1,2}:\d{2}:\d{2})?
            \s+
            (?P<gender>[A-Za-z])\s+
            (?P<address>.+?)\s+
            (?P<zip>\d{5})
            """,
            re.VERBOSE,
        )

        m = pattern.search(clean)
        return m.groupdict() if m else None


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

        # Login Status Frame (ở góc tab bar - chỗ cũ)
        login_status_frame = QWidget()
        login_status_layout = QHBoxLayout(login_status_frame)
        login_status_layout.setContentsMargins(0, 0, 0, 0)
        login_status_layout.setSpacing(8)

        # Login status label
        login_status_label = QLabel("Login status:")
        login_status_label.setStyleSheet("font: bold 11px 'Segoe UI'; color: #2c3e50;")
        login_status_layout.addWidget(login_status_label)

        # Status icon
        self.status_icon = QLabel("⚪")
        self.status_icon.setStyleSheet("""
            font-size: 14px;
            color: white;
            min-width: 20px;
            max-width: 20px;
            min-height: 20px;
            max-height: 20px;
        """)
        self.status_icon.setAlignment(Qt.AlignCenter)
        login_status_layout.addWidget(self.status_icon)

        # Set login status frame as corner widget
        self.notebook.setCornerWidget(login_status_frame)

        # Create Credentials Tab
        self.credentials_tab = self.create_credentials_tab()
        self.notebook.addTab(self.credentials_tab, '🔑 Credentials')

        # Create Tasks Tab
        self.tasks_tab = self.create_tasks_tab()
        self.notebook.addTab(self.tasks_tab, '🎯 Tasks')

        # Log Frame (at bottom)
        self.log_toggle = QPushButton("📋 Activity Log")
        self.log_toggle.clicked.connect(self.toggle_log)
        self.log_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2c3e50;
                border: 1px solid #c5d2df;
                text-align: left;
                font: bold 11px 'Segoe UI';
                padding: 5px;
                margin: 0 3px 3px 3px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        main_layout.addWidget(self.log_toggle)

        self.log_widget = QWidget()
        self.log_widget.setVisible(True)
        self.log_widget.setMaximumHeight(0)
        self.log_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(0)
        self.log_text = PlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(self.log_widget)

        # Redirect stdout to log
        sys.stdout = TextRedirector(self.log_text, "stdout")

        self.log("Application started successfully")
        self.log("Please enter your store credentials and click Login")

    def toggle_log(self):
        collapsed = self.log_widget.maximumHeight() == 0
        if collapsed:
            self.log_widget.setVisible(True)
            self.log_widget.setMaximumHeight(16777215)
            self.log_text.setMaximumHeight(16777215)
            self.log_toggle.setText("📋 Activity Log")
        else:
            self.log_widget.setVisible(False)
            self.log_widget.setMaximumHeight(0)
            self.log_text.setMaximumHeight(0)
            self.log_toggle.setText("📋 Activity Log")

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
        self.credentical_group = ClickableGroupBox("🔑 Credentials", self)
        layout.addWidget(self.credentical_group)

        credentical_layout = QVBoxLayout(self.credentical_group)
        credentical_layout.setSpacing(3)
        credentical_layout.setContentsMargins(4, 2, 4, 4)

        # Account input
        self.account_text = QLineEdit()
        self.account_text.setPlaceholderText('Hotmail/PM/PS')
        self.account_text.setVisible(True)
        credentical_layout.addWidget(self.account_text)

        # Account details inputs
        account_details_layout = QHBoxLayout()
        self.hotmail_id_entry = QLineEdit()
        self.hotmail_id_entry.setPlaceholderText('Hotmail ID')
        self.hotmail_id_entry.setVisible(False)
        account_details_layout.addWidget(self.hotmail_id_entry)
        self.hotmail_password_entry = QLineEdit()
        self.hotmail_password_entry.setPlaceholderText('Hotmail Password')
        self.hotmail_password_entry.setVisible(False)
        account_details_layout.addWidget(self.hotmail_password_entry)
        self.shopify_password_entry = QLineEdit()
        self.shopify_password_entry.setPlaceholderText('Shopify Password')
        self.shopify_password_entry.setVisible(False)
        account_details_layout.addWidget(self.shopify_password_entry)
        self.domain_entry = QLineEdit()
        self.domain_entry.setPlaceholderText('Domain')
        self.domain_entry.setVisible(False)
        account_details_layout.addWidget(self.domain_entry)
        credentical_layout.addLayout(account_details_layout)

        # Name and phone inputs
        name_phone_layout = QHBoxLayout()
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText('Name')
        name_phone_layout.addWidget(self.name_entry, 2)
        self.first_name_entry = QLineEdit()
        self.first_name_entry.setPlaceholderText('First Name')
        self.first_name_entry.setVisible(False)
        name_phone_layout.addWidget(self.first_name_entry, 1)
        self.last_name_entry = QLineEdit()
        self.last_name_entry.setPlaceholderText('Last Name')
        self.last_name_entry.setVisible(False)
        name_phone_layout.addWidget(self.last_name_entry, 1)
        self.phone_entry = QLineEdit()
        self.phone_entry.setPlaceholderText('Phone')
        name_phone_layout.addWidget(self.phone_entry, 1)
        credentical_layout.addLayout(name_phone_layout)

        # Info input
        self.info_text = QLineEdit()
        self.info_text.setPlaceholderText('Info')
        self.info_text.setVisible(True)
        credentical_layout.addWidget(self.info_text)

        # Info details inputs
        info_details_layout = QHBoxLayout()
        self.ssn_entry = QLineEdit()
        self.ssn_entry.setPlaceholderText('SSN')
        self.ssn_entry.setVisible(False)
        info_details_layout.addWidget(self.ssn_entry)
        self.birthday_entry = QLineEdit()
        self.birthday_entry.setPlaceholderText('Birthday')
        self.birthday_entry.setVisible(False)
        info_details_layout.addWidget(self.birthday_entry)
        self.address_entry = QLineEdit()
        self.address_entry.setPlaceholderText('Address')
        self.address_entry.setVisible(False)
        info_details_layout.addWidget(self.address_entry)
        self.zip_entry = QLineEdit()
        self.zip_entry.setPlaceholderText('Zip')
        self.zip_entry.setVisible(False)
        info_details_layout.addWidget(self.zip_entry)
        credentical_layout.addLayout(info_details_layout)

        # Card input
        self.card_text = QLineEdit()
        self.card_text.setPlaceholderText('Card')
        self.card_text.setVisible(True)
        credentical_layout.addWidget(self.card_text)

        # Card details inputs
        card_details_layout = QHBoxLayout()
        self.card_number = QLineEdit()
        self.card_number.setPlaceholderText('Card Number')
        self.card_number.setVisible(False)
        card_details_layout.addWidget(self.card_number)
        self.expired = QLineEdit()
        self.expired.setPlaceholderText('Expired')
        self.expired.setVisible(False)
        card_details_layout.addWidget(self.expired)
        self.cvc = QLineEdit()
        self.cvc.setPlaceholderText('CVC')
        self.cvc.setVisible(False)
        card_details_layout.addWidget(self.cvc)
        credentical_layout.addLayout(card_details_layout)
        seo_group = QGroupBox("⚙️ Preferences")
        layout.addWidget(seo_group)

        seo_layout = QVBoxLayout(seo_group)
        seo_layout.setSpacing(3)
        seo_layout.setContentsMargins(4, 2, 4, 4)

        # SEO Title and Upload Button
        seo_title_layout = QHBoxLayout()
        self.seo_title_entry = QLineEdit()
        self.seo_title_entry.setPlaceholderText('SEO title')
        seo_title_layout.addWidget(self.seo_title_entry)

        self.upload_seo_button = QPushButton("📁 Logo")
        self.upload_seo_button.clicked.connect(self.upload_seo_file)
        seo_title_layout.addWidget(self.upload_seo_button)

        seo_layout.addLayout(seo_title_layout)

        # SEO Description
        self.seo_description_entry = PlainTextEdit()
        self.seo_description_entry.setObjectName("inputText")
        self.seo_description_entry.setPlaceholderText('SEO description')
        self.seo_description_entry.setMaximumHeight(80)
        seo_layout.addWidget(self.seo_description_entry)

        # Pages Frame
        pages_group = QGroupBox("📄 Policies")
        layout.addWidget(pages_group)

        pages_layout = QVBoxLayout(pages_group)
        pages_layout.setSpacing(3)
        pages_layout.setContentsMargins(4, 2, 4, 4)

        # Return & Refund Policy
        self.return_refund_text = PlainTextEdit()
        self.return_refund_text.setObjectName("inputText")
        self.return_refund_text.setPlaceholderText('Return and refund policy...')
        self.return_refund_text.setMaximumHeight(80)
        pages_layout.addWidget(self.return_refund_text)

        # Terms of Service
        self.terms_service_text = PlainTextEdit()
        self.terms_service_text.setObjectName("inputText")
        self.terms_service_text.setPlaceholderText('Terms of service...')
        self.terms_service_text.setMaximumHeight(80)
        pages_layout.addWidget(self.terms_service_text)

        # Shipping Policy
        self.shipping_policy_text = PlainTextEdit()
        self.shipping_policy_text.setObjectName("inputText")
        self.shipping_policy_text.setPlaceholderText('Shipping policy...')
        self.shipping_policy_text.setMaximumHeight(80)
        pages_layout.addWidget(self.shipping_policy_text)

        # Contact Information
        self.contact_info_text = PlainTextEdit()
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
        self.about_us_text = PlainTextEdit()
        self.about_us_text.setObjectName("inputText")
        self.about_us_text.setPlaceholderText('About Us page content...')
        self.about_us_text.setMaximumHeight(80)
        pages_content_layout.addWidget(self.about_us_text)

        # Contact Us
        self.contact_us_text = PlainTextEdit()
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
            setattr(self, f'product_{i}_desc_text', PlainTextEdit())
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

            # Can be enabled later if needed
            # product_item_layout.addLayout(price_layout)

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
            setattr(self, f'image_text_desc_{i}_entry', PlainTextEdit())
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
            setattr(self, f'review_file_{i}_browse_button', QPushButton('📁 Image'))
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
            setattr(self, f'faq_{i}_answer_text', PlainTextEdit())
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

    def toggle_credentials(self):
        """Toggle between compact and detailed view"""
        # Không cần toggle giữa sheet và input nữa vì chỉ dùng GUI fields
        # Chỉ toggle giữa compact view và detailed view
        pass

    def create_tasks_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container = QWidget()
        scroll_area.setWidget(container)

        layout = QVBoxLayout(container)

        # Tasks container (no border wrapper)
        tasks_container = QWidget()
        layout.addWidget(tasks_container)

        tasks_layout = QVBoxLayout(tasks_container)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_layout.setSpacing(8)

        # Tasks grid
        tasks_grid = QWidget()
        tasks_layout.addWidget(tasks_grid)

        tasks_grid_layout = QGridLayout(tasks_grid)
        tasks_grid_layout.setSpacing(3)
        tasks_grid_layout.setContentsMargins(0, 0, 0, 0)

        self.task_buttons = {}
        self.task_data = {}  # Store task metadata
        tasks = [
            ('register_shopify_account', '🆕 Register', register_shopify_account),
            ('install_apps', '📦 Install Apps', install_apps),
            ('link_dser_account', '🛠️ DSers (progress)', link_dser_account),
            ('setup_world_market', '🌍 Markets', setup_world_market),
            ('setup_legal_policies', '📜 Policies', setup_legal_policies),
            ('setup_contact_page', '📄 Pages', setup_contact_page),
            ('setup_shipping_zones', '🚚 Shipping', setup_shipping_zones),
            ('setup_preferences', '⚙️ Preferences', setup_preferences),
            ('connect_domain', '🌐 Connect Domain', connect_domain),
            ('setup_selleasy', '🎯 Selleasy', setup_selleasy),
            ('setup_content_menus', '📋 Content Menus', setup_content_menus),
            ('import_theme', '🎨 Import Themes', import_theme),
            ('setup_notifications', '🔔 Notifications', setup_notifications),
        ]

        # Định nghĩa style chung cho tất cả buttons (tasks + login)
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f9f9f9, stop:1 #e0e0e0);
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                padding: 8px 12px;
                font: 11px 'Segoe UI';
                border-radius: 4px;
                text-align: left;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #e3f2fd);
                color: #1976d2;
                border: 1px solid #2196F3;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
            }
            QPushButton:disabled {
                background-color: #ecf0f1;
                color: #95a5a6;
            }
        """

        # Selected button style (looks like hover)
        self.selected_button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #e3f2fd);
                color: #1976d2;
                border: 1px solid #2196F3;
                padding: 8px 12px;
                font: 11px 'Segoe UI';
                border-radius: 4px;
                text-align: left;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #e3f2fd);
                color: #1976d2;
                border: 1px solid #2196F3;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
            }
            QPushButton:disabled {
                background-color: #ecf0f1;
                color: #95a5a6;
            }
        """

        self.normal_button_style = button_style

        row = 0
        col = 0

        # Thêm Login button đầu tiên
        self.login_button = QPushButton("🔐 Login")
        self.login_button.setStyleSheet(button_style)
        self.login_button.clicked.connect(self.login_action)
        tasks_grid_layout.addWidget(self.login_button, row, col)

        col += 1

        # Thêm các task buttons
        for task_id, task_label, task_func in tasks:
            btn = QPushButton(task_label)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda checked, tid=task_id, tl=task_label, tf=task_func: self.toggle_task_selection(tid, tl, tf))
            tasks_grid_layout.addWidget(btn, row, col)
            self.task_buttons[task_id] = btn
            self.task_data[task_id] = {'label': task_label, 'func': task_func}
            self.task_order.append(task_id)  # Store original order

            col += 1
            if col > 1:
                col = 0
                row += 1

        # Add Run button below task list
        self.run_button = QPushButton("▶️ Run Selected Tasks")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font: bold 12px 'Segoe UI';
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_button.clicked.connect(self.run_selected_tasks)
        self.run_button.setEnabled(False)
        tasks_layout.addWidget(self.run_button)

        layout.addStretch()

        return scroll_area

    def validate_login_inputs(self):
        """Validate input fields for login - only check hotmail_id and shopify_password"""
        # Validate email (từ hotmail_id_entry)
        email = self.hotmail_id_entry.text().strip() if self.hotmail_id_entry.isVisible() else ""
        if not email:
            QMessageBox.critical(self, "Error", "Hotmail ID (Email) is required!")
            return False

        # Validate password (từ shopify_password_entry)
        password = self.shopify_password_entry.text().strip() if self.shopify_password_entry.isVisible() else ""
        if not password:
            QMessageBox.critical(self, "Error", "Shopify Password is required!")
            return False

        return True

    def validate_register_inputs(self):
        """Validate input fields for register - check hotmail_id, zip_code, name, address, card info"""
        # Validate email (từ hotmail_id_entry)
        email = self.hotmail_id_entry.text().strip() if self.hotmail_id_entry.isVisible() else ""
        if not email:
            QMessageBox.critical(self, "Error", "Hotmail ID (Email) is required for registration!")
            return False

        # Validate zip code
        zip_code = self.zip_entry.text().strip() if self.zip_entry.isVisible() else ""
        if not zip_code:
            QMessageBox.critical(self, "Error", "Zip Code is required for registration!")
            return False

        # Validate firstname và lastname
        firstname = self.first_name_entry.text().strip() if self.first_name_entry.isVisible() else ""
        lastname = self.last_name_entry.text().strip() if self.last_name_entry.isVisible() else ""
        if not firstname or not lastname:
            QMessageBox.critical(self, "Error", "First Name and Last Name are required for registration!")
            return False

        # Validate address
        address = self.address_entry.text().strip() if self.address_entry.isVisible() else ""
        if not address:
            QMessageBox.critical(self, "Error", "Address is required for registration!")
            return False

        # Validate card number
        card_number = self.card_number.text().strip() if self.card_number.isVisible() else ""
        if not card_number:
            QMessageBox.critical(self, "Error", "Card Number is required for registration!")
            return False

        # Validate card expired date
        expired = self.expired.text().strip() if self.expired.isVisible() else ""
        if not expired:
            QMessageBox.critical(self, "Error", "Card Expiration Date is required for registration!")
            return False

        # Validate card CVC
        cvc = self.cvc.text().strip() if self.cvc.isVisible() else ""
        if not cvc:
            QMessageBox.critical(self, "Error", "Card CVC is required for registration!")
            return False

        return True

    def validate_inputs(self):
        email = self.hotmail_id_entry.text().strip() if self.hotmail_id_entry.isVisible() else ""
        if not email:
            QMessageBox.critical(self, "Error", "Hotmail ID (Email) is required!")
            return False

        password = self.shopify_password_entry.text().strip() if self.shopify_password_entry.isVisible() else ""
        if not password:
            QMessageBox.critical(self, "Error", "Shopify Password is required!")
            return False

        domain = self.domain_entry.text().strip() if self.domain_entry.isVisible() else ""
        if not domain:
            QMessageBox.critical(self, "Error", "Domain is required!")
            return False

        firstname = self.first_name_entry.text().strip() if self.first_name_entry.isVisible() else ""
        lastname = self.last_name_entry.text().strip() if self.last_name_entry.isVisible() else ""
        if not firstname or not lastname:
            QMessageBox.critical(self, "Error", "First Name and Last Name are required!")
            return False

        seo_title = self.seo_title_entry.text().strip()
        seo_description = self.seo_description_entry.text().strip()
        if not seo_title:
            QMessageBox.critical(self, "Error", "SEO Title is required!")
            return False
        if not seo_description:
            QMessageBox.critical(self, "Error", "SEO Description is required!")
            return False

        return True

    def get_credentials_from_inputs(self):
        email = self.hotmail_id_entry.text().strip() if self.hotmail_id_entry.isVisible() and self.hotmail_id_entry.text().strip() else ""

        password = self.shopify_password_entry.text().strip() if self.shopify_password_entry.isVisible() and self.shopify_password_entry.text().strip() else ""

        domain = self.domain_entry.text().strip() if self.domain_entry.isVisible() and self.domain_entry.text().strip() else ""

        store_id = domain.replace('.', '-').replace('_', '-') if domain else ""

        firstname = self.first_name_entry.text().strip() if self.first_name_entry.isVisible() and self.first_name_entry.text().strip() else ""
        lastname = self.last_name_entry.text().strip() if self.last_name_entry.isVisible() and self.last_name_entry.text().strip() else ""

        ssn = self.ssn_entry.text().strip() if self.ssn_entry.isVisible() and self.ssn_entry.text().strip() else ""
        birthday = self.birthday_entry.text().strip() if self.birthday_entry.isVisible() and self.birthday_entry.text().strip() else ""
        address = self.address_entry.text().strip() if self.address_entry.isVisible() and self.address_entry.text().strip() else ""
        zip_code = self.zip_entry.text().strip() if self.zip_entry.isVisible() and self.zip_entry.text().strip() else ""

        return {
            'storeId': store_id,
            'email': email,
            'password': password,
            'domain': domain,
            'firstname': firstname,
            'lastname': lastname,
            'ssn': ssn,
            'birthday': birthday,
            'address': address,
            'zip': zip_code,
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
        self.log_text.append(f"{message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def setup_driver_and_heartbeat(self) -> Optional[webdriver.Chrome]:
        try:
            self.log("🔧 Setting up Chrome WebDriver with advanced anti-detection...")

            driver = setup_driver()

            if not driver:
                self.log("❌ Failed to initialize WebDriver")
                QMessageBox.critical(self, "Error", "Failed to initialize WebDriver")
                return None

            self.log("✅ WebDriver setup completed with stealth mode")

            self.log("💓 Starting AntiFreeze heartbeat (interval: 15s)...")
            self.heartbeat = AntiFreeze(driver, interval=15)
            self.heartbeat.start()
            self.log("✅ AntiFreeze heartbeat started")

            self.log("🔄 Starting Cloudflare captcha auto-monitor...")
            start_captcha_monitor(driver, check_interval=2.0)
            self.log("✅ Captcha monitor started")

            return driver
        except Exception as e:
            self.log(f"❌ Critical error initializing WebDriver: {e}")
            self.log(f"📋 Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Failed to initialize WebDriver:\n{e}")
            return None

    def login_action(self):
        if self.is_logged_in:
            self.log("⚠️ Already logged in")
            return

        if not self.validate_login_inputs():
            return

        self.credentials = self.get_credentials_from_inputs()

        self.log(f"📝 Credentials validated for store: {self.credentials['storeId']}")
        self.log(f"📧 Email: {self.credentials['email']}")
        self.log(f"👤 Name: {self.credentials['firstname']} {self.credentials['lastname']}")

        self.login_button.setEnabled(False)
        self.hotmail_id_entry.setEnabled(False)
        self.shopify_password_entry.setEnabled(False)
        self.domain_entry.setEnabled(False)
        self.first_name_entry.setEnabled(False)
        self.last_name_entry.setEnabled(False)
        self.seo_title_entry.setEnabled(False)
        self.seo_description_entry.setEnabled(False)

        thread = threading.Thread(target=self.login_thread, daemon=True)
        thread.start()

    def login_thread(self):
        try:
            from utils.element import detect_store_id

            email = self.credentials['email']
            password = self.credentials['password']
            store_id = self.credentials['storeId']

            self.log(f"🔐 Starting login for {email}...")
            self.log(f"📦 Store ID: {store_id}")
            self.log(f"🌐 Domain: {self.credentials['domain']}")

            self.driver = self.setup_driver_and_heartbeat()
            if not self.driver:
                QTimer.singleShot(0, lambda: self.login_button.setEnabled(True))
                return

            self.log("Attempting to login to Shopify...")
            logged = login_to_shopify(self.driver, email, password, store_id)

            if logged:
                self.is_logged_in = True
                self.log("✅ Login successful!")

                detected_store_id = detect_store_id(self.driver)
                if detected_store_id:
                    self.store_id = detected_store_id
                    self.log(f"💾 Store ID saved: {self.store_id}")
                else:
                    self.store_id = store_id
                    self.log(f"💾 Store ID saved (fallback): {self.store_id}")

                QTimer.singleShot(0, self.on_login_success)
            else:
                self.log("❌ Login failed")
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Login Failed", "Could not login to Shopify"))
                QTimer.singleShot(0, self.enable_inputs)
                QTimer.singleShot(0, lambda: self.status_icon.setText("❌"))

                if self.driver:
                    self.cleanup_driver()

        except Exception as e:
            self.log(f"❌ Login error: {e}")
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Login error:\n{e}"))
            QTimer.singleShot(0, self.enable_inputs)
            QTimer.singleShot(0, lambda: self.status_icon.setText("❌"))

            if self.driver:
                self.cleanup_driver()

    def cleanup_driver(self):
        try:
            self.log("🧹 Cleaning up driver resources...")

            stop_captcha_monitor()
            self.log("✅ Captcha monitor stopped")

            if self.heartbeat:
                self.heartbeat.stop()
                self.heartbeat = None
                self.log("✅ AntiFreeze heartbeat stopped")

            if self.driver:
                self.driver.quit()
                self.driver = None
                self.log("✅ Driver closed")

        except Exception as e:
            self.log(f"⚠️ Error during cleanup: {e}")

    def enable_inputs(self):
        self.login_button.setEnabled(True)
        self.hotmail_id_entry.setEnabled(True)
        self.shopify_password_entry.setEnabled(True)
        self.domain_entry.setEnabled(True)
        self.first_name_entry.setEnabled(True)
        self.last_name_entry.setEnabled(True)
        self.seo_title_entry.setEnabled(True)
        self.seo_description_entry.setEnabled(True)
        self.status_icon.setText("⚪")
        self.status_icon.setStyleSheet("""
            font-size: 14px;
            color: white;
            background-color: #95a5a6;
            border-radius: 10px;
            padding: 2px;
            min-width: 20px;
            max-width: 20px;
            min-height: 20px;
            max-height: 20px;
        """)

    def toggle_task_selection(self, task_id, task_label, task_func):
        if task_id in self.selected_tasks:
            self.selected_tasks.discard(task_id)
            self.task_buttons[task_id].setStyleSheet(self.normal_button_style)
            self.log(f"❌ Deselected task: {task_label}")
        else:
            self.selected_tasks.add(task_id)
            self.task_buttons[task_id].setStyleSheet(self.selected_button_style)
            self.log(f"✅ Selected task: {task_label}")

        self.run_button.setEnabled(len(self.selected_tasks) > 0)

    def run_selected_tasks(self):
        if not self.selected_tasks:
            QMessageBox.warning(self, "No Tasks", "Please select at least one task to run.")
            return

        for btn in self.task_buttons.values():
            btn.setEnabled(False)
        self.run_button.setEnabled(False)

        thread = threading.Thread(target=self.run_selected_tasks_thread, daemon=True)
        thread.start()

    def run_selected_tasks_thread(self):
        try:
            self.log(f"\n{'='*60}")
            self.log(f"🚀 Starting {len(self.selected_tasks)} selected task(s)")
            self.log(f"{'='*60}")

            sorted_tasks = [task_id for task_id in self.task_order if task_id in self.selected_tasks]

            for task_id in sorted_tasks:
                task_data = self.task_data[task_id]
                task_func = task_data['func']
                task_label = task_data['label']

                self.log(f"\n▶️ Running: {task_label}")

                self.execute_single_task(task_func, task_label)

                self.log(f"✅ Completed: {task_label}")

            self.log(f"\n{'='*60}")
            self.log(f"✅ All selected tasks completed!")
            self.log(f"{'='*60}\n")

            QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", f"All {len(self.selected_tasks)} selected task(s) completed!"))

        except Exception as e:
            self.log(f"❌ Error running selected tasks: {e}")
            self.log(f"📋 Traceback: {traceback.format_exc()}")
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Error running tasks:\n{e}"))
        finally:
            QTimer.singleShot(0, self.after_run_selected_tasks)

    def after_run_selected_tasks(self):
        for task_id in self.selected_tasks:
            if task_id in self.task_buttons:
                self.task_buttons[task_id].setStyleSheet(self.normal_button_style)
        self.selected_tasks.clear()

        for btn in self.task_buttons.values():
            btn.setEnabled(True)
        self.run_button.setEnabled(False)

    def execute_single_task(self, task_func, task_label):
        if task_func == register_shopify_account:
            if not self.validate_register_inputs():
                raise Exception("Validation failed for register task")

        if not self.credentials:
            self.log("📝 Getting credentials from inputs...")
            self.credentials = self.get_credentials_from_inputs()

        if not self.driver or not self.is_logged_in:
            self.log("🔐 Auto-login required for this task...")

            if not self.driver:
                self.driver = self.setup_driver_and_heartbeat()
                if not self.driver:
                    raise Exception("Failed to setup driver")

            from utils.element import detect_store_id

            email = self.credentials['email']
            password = self.credentials['password']
            store_id = self.credentials['storeId']

            self.log(f"🔐 Logging in as {email}...")
            logged = login_to_shopify(self.driver, email, password, store_id)

            if not logged:
                raise Exception("Auto-login failed")

            self.is_logged_in = True
            self.log("✅ Auto-login successful!")

            detected_store_id = detect_store_id(self.driver)
            if detected_store_id:
                self.store_id = detected_store_id
                self.log(f"💾 Store ID saved: {self.store_id}")
            else:
                self.store_id = store_id
                self.log(f"💾 Store ID saved (fallback): {self.store_id}")

            QTimer.singleShot(0, self.on_login_success)

        store_id = self.store_id if self.store_id else self.credentials['storeId']
        email = self.credentials['email']
        password = self.credentials['password']
        domain = self.credentials['domain']
        firstname = self.credentials['firstname']
        lastname = self.credentials['lastname']
        ssn = self.credentials['ssn']
        birthday = self.credentials['birthday']
        address = self.credentials['address']
        zip_code = self.credentials['zip']

        self.log(f"📦 Using Store ID: {store_id}")

        if task_func == setup_legal_policies:
            policies = self.credentials.get('policies', {})
            task_func(self.driver, store_id, policies)
        elif task_func == setup_preferences:
            seo_data = self.credentials.get('seo', {})
            task_func(self.driver, store_id, seo_data)
        elif task_func == link_dser_account:
            task_func(self.driver, store_id, password)
        elif task_func == register_shopify_account:
            from utils.element import detect_store_id

            name = f"{firstname} {lastname}"
            info = f"{ssn} {birthday} F {address} {zip_code}" if ssn and birthday and address and zip_code else ""
            self.log(f"👤 Registering with name: {name}")
            self.log(f"📋 Info: {info}")
            registered = task_func(self.driver, email, password, store_id, name, info)

            if registered:
                self.log("\n🔍 Detecting store ID after registration...")
                detected_store_id = detect_store_id(self.driver)
                if detected_store_id:
                    self.store_id = detected_store_id
                    self.log(f"💾 Store ID detected and saved: {self.store_id}")
                else:
                    self.store_id = store_id
                    self.log(f"💾 Store ID saved (fallback): {self.store_id}")
        elif task_func == connect_domain:
            task_func(self.driver, store_id, domain)
        elif task_func == setup_notifications:
            clf_token = get_config_json("cloudflare", "8", "token")
            clf_email = get_config_json("cloudflare", "8", "email")
            clf_key = get_config_json("cloudflare", "8", "key")
            self.log(f"🔔 Setting up notifications for domain: {domain}")
            asyncio.run(task_func(self.driver, store_id, domain, clf_token, clf_email, clf_key))
        else:
            task_func(self.driver, store_id)

    def on_login_success(self):
        self.status_icon.setText("✅")
        self.status_icon.setStyleSheet("""
            font-size: 14px;
            color: white;
            background-color: #27ae60;
            border-radius: 10px;
            padding: 2px;
            min-width: 20px;
            max-width: 20px;
            min-height: 20px;
            max-height: 20px;
        """)
        self.login_button.setText("✅ Logged In")
        self.login_button.setEnabled(False)

        for btn in self.task_buttons.values():
            btn.setEnabled(True)

        QMessageBox.information(self, "Success", "Login successful! You can now select and run tasks.")

    def toggle_card_inputs(self):
        if self.is_toggling_card:
            return
        self.is_toggling_card = True

        text = self.card_text.text().strip()
        if text:
            extracted = self.extract_generic_patterns(text)
            if extracted["number"] or extracted["expired"] or extracted["cvc"]:
                self.card_number.setText(extracted["number"] or "")
                self.expired.setText(extracted["expired"] or "")
                self.cvc.setText(extracted["cvc"] or "")
                self.card_text.clear()
                self.card_text.setVisible(False)
                self.card_number.setVisible(True)
                self.expired.setVisible(True)
                self.cvc.setVisible(True)
                self.card_number.setFocus()
            else:
                self.card_number.setText(text)
                self.card_text.clear()
                self.card_text.setVisible(False)
                self.card_number.setVisible(True)
                self.expired.setVisible(True)
                self.cvc.setVisible(True)
                self.card_number.setFocus()
        else:
            if not self.card_number.text().strip() and not self.expired.text().strip() and not self.cvc.text().strip():
                self.card_text.setVisible(True)
                self.card_number.setVisible(False)
                self.expired.setVisible(False)
                self.cvc.setVisible(False)

        self.is_toggling_card = False

    def toggle_info_inputs(self):
        if self.is_toggling_info:
            return
        self.is_toggling_info = True

        text = self.info_text.text().strip()
        if text:
            extracted = self.extract_info(text)
            if extracted and (extracted["ssn"] or extracted["birthday"] or extracted["address"] or extracted["zip"]):
                self.ssn_entry.setText(extracted["ssn"] or "")
                self.birthday_entry.setText(extracted["birthday"] or "")
                self.address_entry.setText(extracted["address"] or "")
                self.zip_entry.setText(extracted["zip"] or "")
                self.info_text.clear()
                self.info_text.setVisible(False)
                self.ssn_entry.setVisible(True)
                self.birthday_entry.setVisible(True)
                self.address_entry.setVisible(True)
                self.zip_entry.setVisible(True)
                self.ssn_entry.setFocus()
            else:
                pass
        else:
            if not self.ssn_entry.text().strip() and not self.birthday_entry.text().strip() and not self.address_entry.text().strip() and not self.zip_entry.text().strip():
                self.info_text.setVisible(True)
                self.ssn_entry.setVisible(False)
                self.birthday_entry.setVisible(False)
                self.address_entry.setVisible(False)
                self.zip_entry.setVisible(False)

        self.is_toggling_info = False

    def toggle_name_inputs(self):
        if self.is_toggling_name:
            return
        self.is_toggling_name = True

        text = self.name_entry.text().strip()
        if text:
            split = self.split_name(text)
            if split["first_name"] or split["last_name"]:
                self.first_name_entry.setText(split["first_name"])
                self.last_name_entry.setText(split["last_name"])
                self.name_entry.clear()
                self.name_entry.setVisible(False)
                self.first_name_entry.setVisible(True)
                self.last_name_entry.setVisible(True)
                self.first_name_entry.setFocus()
        else:
            if not self.first_name_entry.text().strip() and not self.last_name_entry.text().strip():
                self.name_entry.setVisible(True)
                self.first_name_entry.setVisible(False)
                self.last_name_entry.setVisible(False)

        self.is_toggling_name = False

    def toggle_account_inputs(self):
        if self.is_toggling_account:
            return
        self.is_toggling_account = True

        text = self.account_text.text().strip()
        if text:
            try:
                parsed = self.parse_account_string(text)
                if parsed["hotmail_id"] or parsed["hotmail_password"] or parsed["shopify_password"] or parsed["domain"]:
                    self.hotmail_id_entry.setText(parsed["hotmail_id"] or "")
                    self.hotmail_password_entry.setText(parsed["hotmail_password"] or "")
                    self.shopify_password_entry.setText(parsed["shopify_password"] or "")
                    self.domain_entry.setText(parsed["domain"] or "")
                    self.account_text.clear()
                    self.account_text.setVisible(False)
                    self.hotmail_id_entry.setVisible(True)
                    self.hotmail_password_entry.setVisible(True)
                    self.shopify_password_entry.setVisible(True)
                    self.domain_entry.setVisible(True)
                    self.hotmail_id_entry.setFocus()
            except ValueError:
                self.hotmail_id_entry.setText(text)
                self.account_text.clear()
                self.account_text.setVisible(False)
                self.hotmail_id_entry.setVisible(True)
                self.hotmail_password_entry.setVisible(True)
                self.shopify_password_entry.setVisible(True)
                self.domain_entry.setVisible(True)
                self.hotmail_id_entry.setFocus()
        else:
            if not self.hotmail_id_entry.text().strip() and not self.hotmail_password_entry.text().strip() and not self.shopify_password_entry.text().strip() and not self.domain_entry.text().strip():
                self.account_text.setVisible(True)
                self.hotmail_id_entry.setVisible(False)
                self.hotmail_password_entry.setVisible(False)
                self.shopify_password_entry.setVisible(False)
                self.domain_entry.setVisible(False)

        self.is_toggling_account = False

    def shorten_filename(self, filename, max_length=20):
        if len(filename) <= max_length:
            return filename
        else:
            return filename[:7] + "..." + filename[-7:]

    def browse_review_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select Review File {idx}", "", "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.tiff)")
        if file_path:
            setattr(self, f'review_file_{idx}_path', file_path)
            button = getattr(self, f'review_file_{idx}_browse_button')
            button.setText(f"Selected: {self.shorten_filename(os.path.basename(file_path))}")

    def upload_seo_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select SEO File", "", "All Files (*)")
        if file_path:
            self.seo_file_path = file_path
            self.upload_seo_button.setText(f"📁 {self.shorten_filename(os.path.basename(file_path))}")

    def closeEvent(self, event):
        if self.driver:
            reply = QMessageBox.question(self, "Quit", "Do you want to close the browser and exit?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.cleanup_driver()
                    self.log("Browser closed")
                except:
                    pass
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, text):
        self.widget.append(text.rstrip())
        scrollbar = self.widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        sys.__stdout__.write(text)
        sys.__stdout__.flush()

    def flush(self):
        sys.__stdout__.flush()

def main():
    app = QApplication(sys.argv)
    window = StoreAutomationGUI()
    screen = app.primaryScreen().geometry()
    window.move((screen.width() - window.width()) // 2, (screen.height() - window.height()) // 2)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
