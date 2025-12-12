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
from auth import login_to_shopify, register_shopify_account
from utils.captcha import start_captcha_monitor, stop_captcha_monitor
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

class WorkerSignals(QObject):
    """Defines signals available from worker threads"""
    log_message = Signal(str)
    login_success = Signal()
    login_failed = Signal(str)
    task_completed = Signal()
    task_error = Signal(str)
    enable_login_button = Signal()
    enable_inputs = Signal()
    update_status_icon = Signal(str)
    show_message_box = Signal(str, str, str)  # title, message, type (info/critical/warning)

    # Signals để trigger các actions trong Selenium thread
    do_login = Signal(str, str, str)  # email, password, store_id
    do_run_tasks = Signal(set, list, dict, dict, str)  # selected_tasks, task_order, task_data, credentials, store_id


class SeleniumWorker(QObject):
    """
    Worker object để chạy Selenium operations trong thread riêng.
    Tất cả Selenium logic chạy trong thread này để không block GUI.

    Architecture:
    - GUI Thread: Xử lý UI events, render, update widgets
    - Selenium Thread: Chạy driver operations (login, tasks, etc.)
    - Captcha Thread: Monitor và xử lý captcha tự động (đã có sẵn)

    Captcha monitor vẫn hoạt động như cũ - detect và xử lý captcha
    trong thread riêng của nó, can thiệp vào driver khi cần.
    """

    def __init__(self, parent_gui):
        super().__init__()
        self.gui = parent_gui
        self.driver = None
        self.heartbeat = None

        # Connect signals để nhận commands từ GUI thread
        self.gui.signals.do_login.connect(self.perform_login)
        self.gui.signals.do_run_tasks.connect(self.run_tasks)

    @Slot(str, str, str)
    def perform_login(self, email, password, store_id):
        """Thực hiện login - chạy trong Selenium thread"""
        try:
            from utils.element import detect_store_id

            self.gui.signals.log_message.emit(f"🔐 Starting login for {email}...")
            self.gui.signals.log_message.emit(f"📦 Store ID: {store_id}")

            if not self.driver:
                self.driver = self.setup_driver_and_heartbeat()
                if not self.driver:
                    self.gui.signals.enable_login_button.emit()
                    return

            self.gui.signals.log_message.emit("Attempting to login to Shopify...")
            logged = login_to_shopify(self.driver, email, password, store_id)

            if logged:
                self.gui.signals.log_message.emit("✅ Login successful!")

                detected_store_id = detect_store_id(self.driver)
                if detected_store_id:
                    self.gui.store_id = detected_store_id
                else:
                    self.gui.store_id = store_id
                    self.gui.signals.log_message.emit(f"💾 Store ID saved (fallback): {self.gui.store_id}")

                self.gui.signals.login_success.emit()
            else:
                self.gui.signals.log_message.emit("❌ Login failed")
                self.gui.signals.login_failed.emit("Could not login to Shopify")

        except Exception as e:
            self.gui.signals.log_message.emit(f"❌ Login error: {e}")
            self.gui.signals.show_message_box.emit("Error", f"Login error:\n{e}", "critical")
            self.gui.signals.enable_inputs.emit()
            self.gui.signals.update_status_icon.emit("❌")

            self.cleanup_driver()

    @Slot(set, list, dict, dict, str)
    def run_tasks(self, selected_tasks, task_order, task_data, credentials, store_id):
        """Chạy các tasks đã chọn - chạy trong Selenium thread"""
        try:
            self.gui.signals.log_message.emit(f"\n{'='*60}")
            self.gui.signals.log_message.emit(f"🚀 Bắt đầu chạy {len(selected_tasks)} task đã chọn")
            self.gui.signals.log_message.emit(f"{'='*60}")

            # Get tasks in original order
            sorted_tasks = [task_id for task_id in task_order if task_id in selected_tasks]

            self.gui.signals.log_message.emit(f"📋 Danh sách tasks sẽ chạy:")
            for idx, task_id in enumerate(sorted_tasks, 1):
                task_label = task_data[task_id]['label']
                self.gui.signals.log_message.emit(f"   {idx}. {task_label}")
            self.gui.signals.log_message.emit("")

            for idx, task_id in enumerate(sorted_tasks, 1):
                if self.gui.should_stop_tasks:
                    self.gui.signals.log_message.emit("\n⏹️ Đã dừng chạy tasks theo yêu cầu người dùng.")
                    break

                task_func = task_data[task_id]['func']
                task_label = task_data[task_id]['label']

                self.gui.signals.log_message.emit(f"\n▶️ [{idx}/{len(sorted_tasks)}] Đang chạy: {task_label}")

                success = self.execute_single_task(task_func, task_label, credentials, store_id)

                if success is False:
                    self.gui.signals.log_message.emit(f"⏭️ [{idx}/{len(sorted_tasks)}] Bỏ qua: {task_label}")
                    continue

                self.gui.signals.log_message.emit(f"✅ [{idx}/{len(sorted_tasks)}] Hoàn thành: {task_label}")

            if not self.gui.should_stop_tasks:
                self.gui.signals.log_message.emit(f"\n{'='*60}")
                self.gui.signals.log_message.emit(f"✅ ĐÃ HOÀN THÀNH TẤT CẢ {len(selected_tasks)} TASKS!")
                self.gui.signals.log_message.emit(f"{'='*60}\n")

        except Exception as e:
            if not self.gui.should_stop_tasks:
                self.gui.signals.log_message.emit(f"❌ Lỗi khi chạy tasks: {e}")
                self.gui.signals.log_message.emit(f"📋 Traceback: {traceback.format_exc()}")
                self.gui.signals.task_error.emit(f"Lỗi khi chạy tasks:\n{e}")
        finally:
            self.gui.signals.task_completed.emit()

    def setup_driver_and_heartbeat(self) -> Optional[webdriver.Chrome]:
        """Setup driver và các monitors - chạy trong Selenium thread"""
        try:
            self.gui.signals.log_message.emit("🔧 Setting up Chrome WebDriver with advanced anti-detection...")

            driver = setup_driver()

            if not driver:
                self.gui.signals.log_message.emit("❌ Failed to initialize WebDriver")
                self.gui.signals.show_message_box.emit("Error", "Failed to initialize WebDriver", "critical")
                return None

            self.gui.signals.log_message.emit("✅ WebDriver setup completed with stealth mode")

            self.gui.signals.log_message.emit("💓 Starting AntiFreeze heartbeat (interval: 15s)...")
            self.heartbeat = AntiFreeze(driver, interval=15)
            self.heartbeat.start()
            self.gui.signals.log_message.emit("✅ AntiFreeze heartbeat started")

            # Start captcha monitor trong thread riêng của nó
            self.gui.signals.log_message.emit("🔄 Starting Cloudflare captcha auto-monitor...")
            start_captcha_monitor(driver, check_interval=2.0)
            self.gui.signals.log_message.emit("✅ Captcha monitor started (running in separate thread)")

            self.driver = driver
            return driver

        except Exception as e:
            self.gui.signals.log_message.emit(f"❌ Critical error initializing WebDriver: {e}")
            self.gui.signals.log_message.emit(f"📋 Traceback: {traceback.format_exc()}")
            self.gui.signals.show_message_box.emit("Error", f"Failed to initialize WebDriver:\n{e}", "critical")
            return None

    def cleanup_driver(self):
        """
        Cleanup driver và monitors - chạy trong Selenium thread

        ✅ THREAD-SAFE CLEANUP:
        1. Dừng captcha monitor trước (ngăn monitor truy cập driver)
        2. Dừng AntiFreeze heartbeat (ngăn heartbeat truy cập driver)
        3. Quit driver cuối cùng khi không còn thread nào dùng
        """
        try:
            self.gui.signals.log_message.emit("🧹 Cleaning up driver resources...")

            # Stop captcha monitor TRƯỚC - ngăn monitor truy cập driver
            stop_captcha_monitor()
            self.gui.signals.log_message.emit("✅ Captcha monitor stopped")

            # Stop AntiFreeze heartbeat TRƯỚC - ngăn heartbeat truy cập driver
            if self.heartbeat:
                self.heartbeat.stop()
                self.heartbeat = None
                self.gui.signals.log_message.emit("✅ AntiFreeze heartbeat stopped")

            # Quit driver cuối cùng khi không còn thread nào dùng
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.gui.signals.log_message.emit("✅ Driver closed")

        except Exception as e:
            self.gui.signals.log_message.emit(f"⚠️ Error during cleanup: {e}")

    def execute_single_task(self, task_func, task_label, credentials, store_id):
        """Execute một task - chạy trong Selenium thread"""
        # Check if stop was requested before executing
        if self.gui.should_stop_tasks:
            raise Exception("Task stopped by user")

        # Helper function để task có thể check stop flag
        def should_stop():
            return self.gui.should_stop_tasks

        if task_func == register_shopify_account:
            # Validate sẽ được gọi từ GUI thread trước khi đến đây
            pass

        # REGISTER TASK KHÔNG CẦN LOGIN
        if task_func == register_shopify_account:
            self.gui.signals.log_message.emit("🆕 Register task - không cần login trước")
            if not self.driver:
                self.gui.signals.log_message.emit("🔧 Setting up driver and starting monitors...")
                self.driver = self.setup_driver_and_heartbeat()
                if not self.driver:
                    raise Exception("Failed to setup driver")
                self.gui.signals.log_message.emit("✅ Driver setup completed")
        elif not self.driver or not self.gui.is_logged_in:
            # CÁC TASK KHÁC - Cần login trước
            self.gui.signals.log_message.emit("🔐 Auto-login required for this task...")

            if not self.driver:
                self.gui.signals.log_message.emit("🔧 Setting up driver and starting monitors...")
                self.driver = self.setup_driver_and_heartbeat()
                if not self.driver:
                    raise Exception("Failed to setup driver")
                self.gui.signals.log_message.emit("✅ Driver setup completed")

            from utils.element import detect_store_id

            email = credentials['email']
            password = credentials['password']
            cred_store_id = credentials['storeId']

            self.gui.signals.log_message.emit(f"🔐 Logging in as {email}...")
            logged = login_to_shopify(self.driver, email, password, cred_store_id)

            if not logged:
                raise Exception("Auto-login failed")

            self.gui.is_logged_in = True
            self.gui.signals.log_message.emit("✅ Auto-login successful!")

            detected_store_id = detect_store_id(self.driver)
            if detected_store_id:
                self.gui.store_id = detected_store_id
            else:
                self.gui.store_id = cred_store_id
                self.gui.signals.log_message.emit(f"💾 Store ID saved (fallback): {self.gui.store_id}")

            self.gui.signals.login_success.emit()

        # Execute task với parameters tương ứng
        current_store_id = self.gui.store_id if self.gui.store_id else store_id
        email = credentials['email']
        password = credentials['password']
        domain = credentials['domain']
        firstname = credentials['firstname']
        lastname = credentials['lastname']
        ssn = credentials['ssn']
        birthday = credentials['birthday']
        address = credentials['address']
        zip_code = credentials['zip']

        if task_func == setup_legal_policies:
            policies = credentials.get('policies', {})
            task_func(self.driver, current_store_id, policies, should_stop_callback=should_stop)
        elif task_func == setup_preferences:
            seo_data = credentials.get('seo', {})
            task_func(self.driver, current_store_id, seo_data)
        elif task_func == link_dser_account:
            task_func(self.driver, password)
        elif task_func == register_shopify_account:
            from utils.element import detect_store_id

            card_number = credentials.get('card_number', '')
            card_expired = credentials.get('card_expired', '')
            card_cvc = credentials.get('card_cvc', '')

            self.gui.signals.log_message.emit(f"👤 Registering with name: {firstname} {lastname}")
            self.gui.signals.log_message.emit(f"📧 Email: {email}")
            self.gui.signals.log_message.emit(f"🏪 Domain: {domain}")
            self.gui.signals.log_message.emit(f"📍 Address: {address}")
            self.gui.signals.log_message.emit(f"📮 Zip: {zip_code}")
            self.gui.signals.log_message.emit(f"💳 Card number: {'*' * len(card_number) if card_number else 'Not provided'}")

            registered = task_func(self.driver, email, password, domain, firstname, lastname, address, zip_code, card_number, card_expired, card_cvc)

            if registered:
                self.gui.signals.log_message.emit("\n🔍 Detecting store ID after registration...")
                detected_store_id = detect_store_id(self.driver)
                if detected_store_id:
                    self.gui.store_id = detected_store_id
                    self.gui.signals.log_message.emit(f"💾 Store ID detected and saved: {self.gui.store_id}")
                else:
                    self.gui.store_id = current_store_id
                    self.gui.signals.log_message.emit(f"💾 Store ID saved (fallback): {self.gui.store_id}")

                self.gui.is_logged_in = True
                self.gui.signals.login_success.emit()
                self.gui.signals.log_message.emit("✅ Đã đăng ký và đăng nhập thành công!")
        elif task_func == connect_domain:
            task_func(self.driver, current_store_id, domain)
        elif task_func == setup_notifications:
            clf_token = get_config_json("cloudflare", "8", "token")
            clf_email = get_config_json("cloudflare", "8", "email")
            clf_key = get_config_json("cloudflare", "8", "key")
            self.gui.signals.log_message.emit(f"🔔 Setting up notifications for domain: {domain}")
            asyncio.run(task_func(self.driver, current_store_id, domain, clf_token, clf_email, clf_key))
        elif task_func == install_apps or task_func == setup_shipping_zones:
            # Truyền callback cho các task hỗ trợ stop
            task_func(self.driver, current_store_id, should_stop_callback=should_stop)
        else:
            # Các task còn lại chưa có stop callback
            task_func(self.driver, current_store_id)

        return True

class StoreAutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autify")
        self.resize(600, 700)
        self.setFixedSize(600, 700)
        self.setWindowIcon(QIcon(os.path.join(base_path, 'favicon.ico')))

        self._driver_ref = None  # Chỉ dùng để check, không dùng trực tiếp
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
        self.is_running_tasks = False  # Track if tasks are currently running
        self.should_stop_tasks = False  # Flag to stop tasks

        # Initialize worker signals (no parent = thread-safe for cross-thread signals)
        self.signals = WorkerSignals()

        # Selenium worker sẽ chạy trong thread riêng
        self.selenium_worker = None
        self.selenium_thread = None

        self.setup_styles()
        self.create_widgets()

        # Connect signals AFTER widgets are created
        self.connect_signals()

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

    @property
    def driver(self):
        """Property để access driver từ selenium worker"""
        if self.selenium_worker:
            return self.selenium_worker.driver
        return None

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

        # Thêm Login button đầu tiên (để test khi cần)
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

        # Add Run and Stop buttons in horizontal layout
        buttons_layout = QHBoxLayout()

        self.run_button = QPushButton("▶️ Run Selected Tasks")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font: bold 12px 'Segoe UI';
                border-radius: 4px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #45a049;
                cursor: pointer;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.setFocusPolicy(Qt.StrongFocus)
        self.run_button.clicked.connect(self.run_selected_tasks)
        self.run_button.setEnabled(False)
        self.run_button.setToolTip("Chạy các task đã chọn")
        buttons_layout.addWidget(self.run_button)

        self.stop_button = QPushButton("⏹️ Stop Tasks")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font: bold 12px 'Segoe UI';
                border-radius: 4px;
                min-height: 35px;
            }
            QPushButton:hover:!disabled {
                background-color: #da190b;
            }
            QPushButton:pressed:!disabled {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                cursor: not-allowed;
            }
            QPushButton:!disabled {
                cursor: pointer;
            }
        """)
        self.stop_button.clicked.connect(self.stop_tasks)
        self.stop_button.setEnabled(False)
        self.stop_button.setToolTip("Dừng các task đang chạy")
        buttons_layout.addWidget(self.stop_button)

        tasks_layout.addLayout(buttons_layout)

        layout.addStretch()

        return scroll_area

    def validate_login_inputs(self):
        """Validate input fields for login - only check hotmail_id and shopify_password"""
        # Validate email (from parsed hotmail_id_entry field)
        email = self.hotmail_id_entry.text().strip()
        if not email:
            QMessageBox.critical(self, "Error", "Hotmail ID (Email) is required for login!")
            return False

        # Validate password (from parsed shopify_password_entry field)
        password = self.shopify_password_entry.text().strip()
        if not password:
            QMessageBox.critical(self, "Error", "Shopify Password is required for login!")
            return False

        return True

    def show_error_thread_safe(self, message):
        """Show error message in a thread-safe way"""
        if QThread.currentThread() != self.thread():
            self.signals.show_message_box.emit("Error", message, "critical")
        else:
            QMessageBox.critical(self, "Error", message)

    def validate_register_inputs(self):
        email = self.hotmail_id_entry.text().strip()
        if not email:
            self.show_error_thread_safe("Hotmail ID (Email) is required for registration!")
            return False

        shopify_password = self.shopify_password_entry.text().strip()
        if not shopify_password:
            self.show_error_thread_safe("Shopify Password is required for registration!")
            return False

        domain = self.domain_entry.text().strip()
        if not domain:
            self.show_error_thread_safe("Domain is required for registration!")
            return False

        firstname = self.first_name_entry.text().strip()
        if not firstname:
            self.show_error_thread_safe("First Name is required for registration!")
            return False

        lastname = self.last_name_entry.text().strip()
        if not lastname:
            self.show_error_thread_safe("Last Name is required for registration!")
            return False

        address = self.address_entry.text().strip()
        if not address:
            self.show_error_thread_safe("Address is required for registration!")
            return False

        zip_code = self.zip_entry.text().strip()
        if not zip_code:
            self.show_error_thread_safe("Zip Code is required for registration!")
            return False

        card_number = self.card_number.text().strip()
        if not card_number:
            self.show_error_thread_safe("Card Number is required for registration!")
            return False

        expired = self.expired.text().strip()
        if not expired:
            self.show_error_thread_safe("Card Expiration Date is required for registration!")
            return False

        cvc = self.cvc.text().strip()
        if not cvc:
            self.show_error_thread_safe("Card CVC is required for registration!")
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
        # Debug: Log raw input values
        self.log("🔍 DEBUG - Reading input fields:")

        email = self.hotmail_id_entry.text().strip()
        self.log(f"  Email field value: '{email}' (visible: {self.hotmail_id_entry.isVisible()})")

        password = self.shopify_password_entry.text().strip()
        self.log(f"  Password field value: '{password}' (visible: {self.shopify_password_entry.isVisible()})")

        domain = self.domain_entry.text().strip()
        self.log(f"  Domain field value: '{domain}' (visible: {self.domain_entry.isVisible()})")

        store_id = domain.replace('.', '-').replace('_', '-') if domain else ""

        firstname = self.first_name_entry.text().strip()
        self.log(f"  First name field value: '{firstname}' (visible: {self.first_name_entry.isVisible()})")

        lastname = self.last_name_entry.text().strip()
        self.log(f"  Last name field value: '{lastname}' (visible: {self.last_name_entry.isVisible()})")

        # Lấy giá trị từ các field bất kể visible hay không (chỉ cần có giá trị)
        ssn = self.ssn_entry.text().strip()
        birthday = self.birthday_entry.text().strip()
        address = self.address_entry.text().strip()
        zip_code = self.zip_entry.text().strip()

        self.log(f"  Address field value: '{address}' (visible: {self.address_entry.isVisible()})")
        self.log(f"  Zip field value: '{zip_code}' (visible: {self.zip_entry.isVisible()})")

        card_number = self.card_number.text().strip()
        card_expired = self.expired.text().strip()
        card_cvc = self.cvc.text().strip()

        self.log(f"  Card number field value: '{'*' * len(card_number) if card_number else ''}' (visible: {self.card_number.isVisible()})")
        self.log(f"  Card expired field value: '{card_expired}' (visible: {self.expired.isVisible()})")
        self.log(f"  Card CVC field value: '{'*' * len(card_cvc) if card_cvc else ''}' (visible: {self.cvc.isVisible()})")

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
            'card_number': card_number,
            'card_expired': card_expired,
            'card_cvc': card_cvc,
            'seo': {
                'title': self.seo_title_entry.text().strip(),
                'description': self.seo_description_entry.toPlainText().strip()
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
            ],
            'policies': {
                'return_and_refund': self.return_refund_text.toPlainText().strip(),
                'terms_of_service': self.terms_service_text.toPlainText().strip(),
                'shipping': self.shipping_policy_text.toPlainText().strip(),
                'contact_information': self.contact_info_text.toPlainText().strip()
            }
        }

    def connect_signals(self):
        """Connect worker signals to GUI slots using Qt.QueuedConnection for thread safety"""
        self.signals.log_message.connect(self.log_safe, Qt.QueuedConnection)
        self.signals.login_success.connect(self.on_login_success, Qt.QueuedConnection)
        self.signals.login_failed.connect(self.on_login_failed, Qt.QueuedConnection)
        self.signals.task_completed.connect(self.after_run_selected_tasks, Qt.QueuedConnection)
        self.signals.task_error.connect(self.on_task_error, Qt.QueuedConnection)
        self.signals.enable_login_button.connect(lambda: self.login_button.setEnabled(True), Qt.QueuedConnection)
        self.signals.enable_inputs.connect(self.enable_inputs, Qt.QueuedConnection)
        self.signals.update_status_icon.connect(self.update_status_icon, Qt.QueuedConnection)
        self.signals.show_message_box.connect(self.show_message_box_safe, Qt.QueuedConnection)

    def log(self, message):
        """Thread-safe logging - can be called from any thread"""
        if QThread.currentThread() == self.thread():
            # Called from main thread
            self.log_safe(message)
        else:
            # Called from worker thread - use signal
            self.signals.log_message.emit(message)

    def log_safe(self, message):
        """Actually append to log - only called from main thread"""
        self.log_text.append(f"{message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_status_icon(self, icon_text):
        """Update status icon from main thread"""
        self.status_icon.setText(icon_text)

    def show_message_box_safe(self, title, message, msg_type):
        """Show message box from main thread"""
        if msg_type == "info":
            QMessageBox.information(self, title, message)
        elif msg_type == "critical":
            QMessageBox.critical(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)

    def on_login_failed(self, error_msg):
        """Handle login failure from main thread - THREAD-SAFE VERSION"""
        QMessageBox.critical(self, "Login Failed", error_msg)
        self.enable_inputs()
        self.status_icon.setText("❌")

        # ✅ FIXED: GUI thread KHÔNG truy cập driver trực tiếp
        # Driver thuộc về Selenium thread, sẽ được cleanup bởi Selenium worker
        # Tránh race condition giữa GUI thread và Selenium thread

    def on_task_error(self, error_msg):
        """Handle task error from main thread"""
        # QMessageBox.critical(self, "Error", error_msg)  # Removed modal as per user request, logs are sufficient

    def create_selenium_worker(self):
        """Tạo Selenium worker và thread riêng"""
        # Tạo thread mới cho Selenium
        self.selenium_thread = QThread()

        # Tạo worker và move vào thread
        self.selenium_worker = SeleniumWorker(self)
        self.selenium_worker.moveToThread(self.selenium_thread)

        # Start thread
        self.selenium_thread.start()

        self.log("✅ Selenium worker thread đã được tạo và khởi động")

    def cleanup_selenium_worker(self):
        """Cleanup Selenium worker và thread"""
        if self.selenium_worker:
            # Cleanup driver trong worker
            self.selenium_worker.cleanup_driver()

        if self.selenium_thread:
            self.selenium_thread.quit()
            self.selenium_thread.wait()

        self.selenium_worker = None
        self.selenium_thread = None

    def login_action(self):
        if self.is_logged_in:
            self.log("⚠️ Already logged in")
            return

        # Disable button ngay để tránh click nhiều lần
        self.login_button.setEnabled(False)

        if not self.validate_login_inputs():
            # Re-enable button nếu validation failed
            self.login_button.setEnabled(True)
            return

        # Get credentials from input fields FIRST
        self.credentials = self.get_credentials_from_inputs()

        # NOW log the credentials that were just retrieved
        self.log(f"📝 Credentials retrieved from input fields:")
        self.log(f"📦 Store ID: {self.credentials['storeId']}")
        self.log(f"📧 Email: {self.credentials['email']}")
        self.log(f"👤 Name: {self.credentials['firstname']} {self.credentials['lastname']}")

        # Disable inputs during login (button đã disable ở trên rồi)
        self.hotmail_id_entry.setEnabled(False)
        self.shopify_password_entry.setEnabled(False)
        self.domain_entry.setEnabled(False)
        self.first_name_entry.setEnabled(False)
        self.last_name_entry.setEnabled(False)
        self.seo_title_entry.setEnabled(False)
        self.seo_description_entry.setEnabled(False)

        # Tạo Selenium worker nếu chưa có
        if not self.selenium_worker:
            self.create_selenium_worker()

        # Chạy login trong Selenium thread qua signal
        email = self.credentials['email']
        password = self.credentials['password']
        store_id = self.credentials['storeId']

        self.signals.do_login.emit(email, password, store_id)

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
        """Toggle task selection - does NOT run the task immediately

        CHÚ Ý: Hàm này CHỈ chọn/bỏ chọn task, KHÔNG chạy task!
        Phải click nút 'Run Selected Tasks' để chạy các task đã chọn.
        """
        self.log(f"🖱️ Click vào task button: {task_label}")
        self.log(f"⚠️ CHÚ Ý: CHỈ ĐANG CHỌN/BỎ CHỌN, KHÔNG CHẠY TASK!")

        if task_id in self.selected_tasks:
            self.selected_tasks.discard(task_id)
            self.task_buttons[task_id].setStyleSheet(self.normal_button_style)
            self.log(f"❌ Đã BỎ CHỌN task: {task_label} (chưa chạy gì cả)")
        else:
            self.selected_tasks.add(task_id)
            self.task_buttons[task_id].setStyleSheet(self.selected_button_style)
            self.log(f"✅ Đã CHỌN task: {task_label} (chưa chạy, chỉ đánh dấu)")

        # Enable Run button if any tasks are selected
        self.run_button.setEnabled(len(self.selected_tasks) > 0)

        # Log current selection count
        if len(self.selected_tasks) > 0:
            self.log(f"📋 Tổng số task đã chọn: {len(self.selected_tasks)}")
            self.log(f"👉 Nhấn nút 'Run Selected Tasks' ở dưới để BẮT ĐẦU CHẠY các task!")
        else:
            self.log(f"📋 Không có task nào được chọn")

    def run_selected_tasks(self):
        self.log("🖱️ Run button được click!")

        if not self.selected_tasks:
            self.log("⚠️ Không có task nào được chọn")
            QMessageBox.warning(self, "Không có task nào", "Vui lòng chọn ít nhất một task trước khi chạy.")
            return

        self.log("\n" + "="*60)
        self.log(f"▶️ BẮT ĐẦU CHẠY {len(self.selected_tasks)} TASK ĐÃ CHỌN")
        self.log("="*60)

        self.should_stop_tasks = False
        self.is_running_tasks = True

        for btn in self.task_buttons.values():
            btn.setEnabled(False)
        self.run_button.setEnabled(False)

        self.stop_button.setEnabled(True)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setFocus()  # Set focus to make it more visible
        self.log("✅ Stop button đã được enable và có thể click")

        # Get credentials nếu chưa có
        if not self.credentials:
            self.log("📝 Getting credentials from inputs...")
            self.credentials = self.get_credentials_from_inputs()

        # Tạo Selenium worker nếu chưa có
        if not self.selenium_worker:
            self.create_selenium_worker()

        # Chạy tasks trong Selenium thread qua signal
        self.signals.do_run_tasks.emit(
            self.selected_tasks.copy(),  # Copy để tránh race condition
            self.task_order.copy(),
            self.task_data.copy(),
            self.credentials.copy(),
            self.store_id if self.store_id else self.credentials['storeId']
        )

    def stop_tasks(self):
        """Stop currently running tasks - CHỈ set flag, thread sẽ tự dừng"""
        self.log("🖱️ Stop button được click!")
        self.log(f"🔍 Debug - is_running_tasks: {self.is_running_tasks}")
        self.log(f"🔍 Debug - stop_button enabled: {self.stop_button.isEnabled()}")

        if not self.is_running_tasks:
            self.log("⚠️ Không có task nào đang chạy")
            return

        self.log("\n" + "="*60)
        self.log("⏹️ ĐANG DỪNG TASKS - Vui lòng đợi thread kết thúc...")
        self.log("="*60)

        # Chỉ set flag để thread tự dừng
        # Thread sẽ emit task_completed signal và cleanup được xử lý ở đó
        self.should_stop_tasks = True
        self.stop_button.setEnabled(False)
        self.stop_button.setCursor(Qt.ArrowCursor)
        self.log("✅ Đã set stop flag. Thread sẽ dừng và cleanup tự động.")

        # KHÔNG gọi cleanup_and_reset ở đây
        # Để after_run_selected_tasks() xử lý khi thread kết thúc



    def after_run_selected_tasks(self):
        if self.should_stop_tasks:
            self.log("⏹️ Tasks đã bị DỪNG - Reset về trạng thái sẵn sàng")
        else:
            self.log("✅ Tasks đã HOÀN THÀNH - Reset về trạng thái sẵn sàng")

        self.is_running_tasks = False
        self.should_stop_tasks = False

        # Clear all task selections và reset button styles
        for task_id in list(self.selected_tasks):
            if task_id in self.task_buttons:
                self.task_buttons[task_id].setStyleSheet(self.normal_button_style)
        self.selected_tasks.clear()

        for btn in self.task_buttons.values():
            btn.setEnabled(True)

        self.run_button.setEnabled(False)

        self.stop_button.setEnabled(False)
        self.stop_button.setCursor(Qt.ArrowCursor)

        if self.is_logged_in:
            self.login_button.setText("✅ Logged In")
            self.login_button.setEnabled(False)
            self.log("💡 Login state được giữ nguyên. Browser vẫn mở. Sẵn sàng chạy task mới!")

        self.log("="*60 + "\n")

        self.log_text.clear()
        self.log("🔄 Log đã được clear. Sẵn sàng cho lần chạy tiếp theo.")
        if self.is_logged_in:
            self.log("✅ Đã đăng nhập. Có thể chọn và chạy tasks.")
        else:
            self.log("⚠️ Chưa đăng nhập. Sẽ auto-login khi chạy tasks.")

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

        # Task buttons luôn enabled (không cần login trước)
        for btn in self.task_buttons.values():
            btn.setEnabled(True)

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
        # Check if selenium worker has driver
        has_driver = self.selenium_worker and self.selenium_worker.driver

        if has_driver:
            reply = QMessageBox.question(self, "Quit", "Do you want to close the browser and exit?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.cleanup_selenium_worker()
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
