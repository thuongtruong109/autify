import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional
import inquirer

# Import utility functions
from utils import load_credentials

# Import feature modules
from auth import login_to_shopify
from install import install_apps
from dsers import handle_dser_open_and_confirm
from market import setup_world_market
from policies import setup_legal_policies
from pages import setup_contact_page
from shipping import setup_shipping_zones

def setup_driver() -> Optional[webdriver.Chrome]:
    """Setup và khởi tạo Chrome WebDriver với session lưu trữ"""
    try:
        print("Setting up Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        # LƯU SESSION VÀO FOLDER selenium_data
        user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selenium_data")
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Tắt các thông báo không cần thiết
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng khi khởi tạo WebDriver. Chi tiết: {e}")
        print("Vui lòng kiểm tra xem Chrome đã được cài đặt và không có phiên Selenium nào đang chạy ngầm.")
        return None

def show_interactive_menu():
    """Hiển thị menu interactive để chọn các functions muốn chạy"""
    print("\n" + "="*80)
    print("🎯 CHỌN CÁC TASKS BẠN MUỐN CHẠY")
    print("="*80)
    print("📌 Sử dụng phím ↑/↓ để di chuyển")
    print("📌 Nhấn SPACE để chọn/bỏ chọn")
    print("📌 Nhấn ENTER để xác nhận và chạy")
    print("="*80 + "\n")

    # Định nghĩa các options
    task_options = [
        ('install_apps', '📦 Cài đặt Apps'),
        ('handle_dser_open_and_confirm', '🛠️  Xử lý DSers Open & Confirm'),
        ('setup_world_market', '🌍 Cài đặt World Market'),
        ('setup_legal_policies', '📜 Cài đặt Legal Policies'),
        ('setup_contact_page', '📄 Cài đặt Contact Page'),
        ('setup_shipping_zones', '🚚 Cài đặt Shipping Zones'),
    ]

    # Tạo câu hỏi checkbox
    questions = [
        inquirer.Checkbox(
            'tasks',
            message="Chọn các tasks bạn muốn chạy",
            choices=[label for _, label in task_options],
            default=[]  # Không chọn mặc định, để trống
        ),
    ]

    # Hiển thị menu và lấy kết quả
    try:
        answers = inquirer.prompt(questions)
        if not answers or not answers['tasks']:
            print("\n⚠️  Không có task nào được chọn. Thoát chương trình.")
            return []

        # Map labels trở lại function names
        selected_labels = set(answers['tasks'])
        selected_tasks = [func_name for func_name, label in task_options if label in selected_labels]

        print(f"\n✅ Đã chọn {len(selected_tasks)} task(s):")
        for task in selected_tasks:
            print(f"   - {task}")
        print()

        return selected_tasks
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi người dùng. Thoát chương trình.")
        return []

def main():
    """Main execution function"""
    # Load credentials (chỉ một object duy nhất)
    entry = load_credentials()
    if not entry:
        print("No valid credentials found. Exiting.")
        return

    email, password, storeId = entry["email"], entry["password"], entry["storeId"]

    print(f"\n{'='*60}")
    print(f"📌 SỬ DỤNG STORE: {storeId}")
    print(f"📌 EMAIL: {email}")
    print(f"{'='*60}\n")

    # Hiển thị menu để chọn tasks
    selected_tasks = show_interactive_menu()
    if not selected_tasks:
        return

    # Setup WebDriver
    driver = setup_driver()
    if not driver:
        return

    try:
        # BƯỚC 1: LOGIN (luôn chạy)
        print("\n🔐 BƯỚC 1: ĐĂNG NHẬP VÀO SHOPIFY...")
        print("="*60)
        logged = login_to_shopify(driver, email, password, storeId)

        if not logged:
            print("🚫 Cannot proceed. Login failed.")
            return

        print("\n✅ ĐĂNG NHẬP THÀNH CÔNG!")
        print("="*60)

        # Chạy các tasks đã chọn
        if 'install_apps' in selected_tasks:
            print("\n📦 BƯỚC 2: CÀI ĐẶT APPS...")
            print("="*60)
            install_apps(driver, storeId)

        if 'handle_dser_open_and_confirm' in selected_tasks:
            print("\n🛠️ BƯỚC 3: XỬ LÝ DSERS OPEN VÀ CONFIRM...")
            print("="*60)
            handle_dser_open_and_confirm(driver, storeId)

        if 'setup_world_market' in selected_tasks:
            print("\n🌍 BƯỚC 4: CÀI ĐẶT WORLD MARKET...")
            print("="*60)
            setup_world_market(driver, storeId)

        if 'setup_legal_policies' in selected_tasks:
            print("\n📜 BƯỚC 5: CÀI ĐẶT LEGAL POLICIES...")
            print("="*60)
            setup_legal_policies(driver, storeId, entry.get("policies", {}))

        if 'setup_contact_page' in selected_tasks:
            print("\n📄 BƯỚC 6: CÀI ĐẶT CONTACT PAGE...")
            print("="*60)
            setup_contact_page(driver, storeId)

        if 'setup_shipping_zones' in selected_tasks:
            print("\n🚚 BƯỚC 7: CÀI ĐẶT SHIPPING ZONES...")
            print("="*60)
            setup_shipping_zones(driver, storeId)

    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
    finally:
        # ⚠️ GIỮ BROWSER MỞ - Chờ user xác nhận trước khi đóng
        print("\n" + "="*80)
        print("✅ [Hoàn thành] Tất cả các tác vụ đã hoàn tất.")
        print("📌 Browser sẽ VẪN MỞ để bạn kiểm tra kết quả.")
        print("🔴 Nhấn Enter ở đây khi bạn MUỐN ĐÓNG browser...")
        print("="*80)
        input()

        try:
            driver.quit()
            print("✅ Browser đã được đóng thành công.")
        except:
            print("⚠️ Browser có thể đã được đóng thủ công.")

if __name__ == "__main__":
    main()