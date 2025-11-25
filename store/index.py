import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional
import inquirer

from utils import load_credentials

from auth import login_to_shopify
from install import install_apps
from dsers import handle_dser_open_and_confirm
from market import setup_world_market
from policies import setup_legal_policies
from pages import setup_contact_page
from shipping import setup_shipping_zones
from themes import setup_preferences

def setup_driver() -> Optional[webdriver.Chrome]:
    try:
        print("Setting up Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        # SAVE SESSION TO selenium_data FOLDER
        user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selenium_data")
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Disable unnecessary logs
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-extensions")

        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Critical error initializing WebDriver. Details: {e}")
        print("Please check if Chrome is installed and no Selenium sessions are running in the background.")
        return None

def show_interactive_menu():
    print("\n" + "="*80)
    print("🎯 SELECT THE TASKS YOU WANT TO RUN")
    print("="*80)
    print("📌 Use ↑/↓ keys to navigate")
    print("📌 Press SPACE to select/deselect")
    print("📌 Press ENTER to confirm and run")
    print("="*80 + "\n")

    task_options = [
        ('login', '🔐 Login'),
        ('install_apps', '📦 Install Apps'),
        ('handle_dser_open_and_confirm', '🛠️  DSers (progress)'),
        ('setup_world_market', '🌍 Markets'),
        ('setup_legal_policies', '📜 Policies'),
        ('setup_contact_page', '📄 Pages'),
        ('setup_shipping_zones', '🚚 Shipping (progress)'),
        ('setup_preferences', '⚙️  Preferences'),
    ]

    questions = [
        inquirer.Checkbox(
            'tasks',
            message="Select the tasks you want to run",
            choices=[label for _, label in task_options],
            default=[]
        ),
    ]

    try:
        answers = inquirer.prompt(questions)
        if not answers or not answers['tasks']:
            print("\n⚠️  No tasks selected. Exiting program.")
            return []

        selected_labels = set(answers['tasks'])
        selected_tasks = [func_name for func_name, label in task_options if label in selected_labels]

        print(f"\n✅ Selected {len(selected_tasks)} task(s):")
        for task in selected_tasks:
            print(f"   - {task}")
        print()

        return selected_tasks
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user. Exiting program.")
        return []

def main():
    # Mặc định sử dụng Google Sheet, lấy từ row đầu tiên (index 0)
    # Nếu muốn dùng config.json, đổi use_sheet=False
    entry = load_credentials(use_sheet=True, row_index=0)
    if not entry:
        print("No valid credentials found. Exiting.")
        return

    email, password, storeId = entry["email"], entry["password"], entry["storeId"]

    selected_tasks = show_interactive_menu()
    if not selected_tasks:
        return

    driver = setup_driver()
    if not driver:
        return

    try:
        # Chỉ login nếu user chọn task "login" hoặc có task khác cần thực hiện
        if 'login' in selected_tasks or len(selected_tasks) > 0:
            print("\n🔐 Login to Shopify...")
            print("="*60)
            logged = login_to_shopify(driver, email, password, storeId)

            if not logged:
                print("🚫 Cannot proceed. Login failed.")
                return

            print("\n✅ Login successful!")
            print("="*60)

        # Nếu user chỉ chọn "login", không chạy các task khác
        if selected_tasks == ['login']:
            print("\n✅ Login completed. No other tasks selected.")
        else:
            # Chạy các task khác (bỏ qua 'login' vì đã thực hiện ở trên)
            if 'install_apps' in selected_tasks:
                install_apps(driver, storeId)

            if 'handle_dser_open_and_confirm' in selected_tasks:
                handle_dser_open_and_confirm(driver, storeId, password)

            if 'setup_world_market' in selected_tasks:
                setup_world_market(driver, storeId)

            if 'setup_legal_policies' in selected_tasks:
                setup_legal_policies(driver, storeId, entry.get("policies", {}))

            if 'setup_contact_page' in selected_tasks:
                setup_contact_page(driver, storeId)

            if 'setup_shipping_zones' in selected_tasks:
                setup_shipping_zones(driver, storeId)

            if 'setup_preferences' in selected_tasks:
                setup_preferences(driver, storeId)

    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
    finally:
        print("\n" + "="*80)
        print("✅ [Completed] All tasks have been completed.")
        print("📌 The browser will REMAIN OPEN for you to check the results.")
        print("🔴 Press Enter here when you WANT TO CLOSE the browser...")
        print("="*80)
        input()

        try:
            driver.quit()
            print("✅ Browser has been closed successfully.")
        except:
            print("⚠️ Browser may have been closed manually.")

if __name__ == "__main__":
    main()