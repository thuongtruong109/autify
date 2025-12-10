import inquirer
import pickle
import asyncio

from configs.driver import setup_driver
from configs.anti_freeze import AntiFreeze

from configs.app import load_credentials, get_config_json
from utils.element import detect_store_id
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

# Global variable to store the store_id after login
_store_id = None

def check_login_required(driver, email: str, password: str, storeId: str, selected_tasks: list) -> bool:
    """
    Middleware function to check if login is required before executing tasks.

    Args:
        driver: Selenium WebDriver instance
        email: User email
        password: User password
        storeId: Store ID
        selected_tasks: List of selected tasks to run

    Returns:
        bool: True if login successful or not required, False otherwise
    """
    global _store_id

    # Nếu chỉ có task register thì không cần login
    if selected_tasks == ['register_shopify_account']:
        return True

    # Kiểm tra xem đã đăng nhập chưa
    print("\n🔍 Checking login status...")
    print("="*60)

    current_store_id = detect_store_id(driver)
    if not current_store_id:
        print("⚠️ Not logged in. Starting login process...")
        logged = login_to_shopify(driver, email, password, storeId)

        if not logged:
            print("🚫 Login failed. Cannot proceed with tasks.")
            return False

        print("✅ Login successful!")
        # Lấy store_id sau khi login thành công
        _store_id = detect_store_id(driver)
        if not _store_id:
            _store_id = storeId  # Fallback về storeId từ entry nếu không detect được
    else:
        print("✅ Already logged in. Proceeding with tasks...")
        _store_id = current_store_id

    print("="*60)
    return True

def show_interactive_menu():
    print("\n" + "="*80 + "\n")
    print("📌 Use ↑/↓ keys to navigate")
    print("📌 Press SPACE to select/deselect")
    print("📌 Press ENTER to confirm and run\n")

    task_options = [
        ('register_shopify_account', '🆕 Register'),
        ('login', '🔐 Login'),
        ('install_apps', '📦 Install Apps'),
        ('link_dser_account', '🛠️  DSers (link account)'),
        ('connect_domain', '🌐 Domain'),
        ('setup_world_market', '🌍 Markets'),
        ('setup_legal_policies', '📜 Policies'),
        ('setup_contact_page', '📄 Pages'),
        ('setup_shipping_zones', '🚚 Shipping'),
        ('setup_preferences', '⚙️  Preferences'),
        ('setup_selleasy', '🎯 Selleasy'),
        ('setup_content_menus', '📋 Content Menus'),
        ('import_themes', '🎨 Import Themes'),
        ('setup_notifications', '🔔 Notifications'),
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

async def main():
    # Mặc định sử dụng Google Sheet, lấy từ row đầu tiên (index 0)
    # Nếu muốn dùng env.json, đổi use_sheet=False
    entry = load_credentials(use_sheet=True, row_index=0)
    if not entry:
        print("No valid credentials found. Exiting.")
        return

    email, password, storeId, domain, name, info = entry["email"], entry["password"], entry["storeId"], entry["domain"], entry["name"], entry["info"]

    selected_tasks = show_interactive_menu()
    if not selected_tasks:
        return

    driver = setup_driver()
    if not driver:
        return

    start_captcha_monitor(driver, check_interval=1.5)

    heartbeat = AntiFreeze(driver, interval=15)
    heartbeat.start()

    try:
        # Xử lý task register (không cần login)
        if 'register_shopify_account' in selected_tasks:
            print("\n🆕 Starting registration process...")
            print("="*60)
            registered = register_shopify_account(driver, email, password, storeId, name, info)
            if not registered:
                print("🚫 Registration failed. Cannot proceed.")
                return
            print(f"\n✅ Registration successful for {name}!")
            print("="*60)

            # Sau khi register xong, nếu có tasks khác thì cần login và lưu store_id
            if len(selected_tasks) > 1:
                print("\n🔍 Detecting store ID after registration...")
                _store_id = detect_store_id(driver)
                if _store_id:
                    print(f"💾 Store ID detected and saved: {_store_id}")
                else:
                    _store_id = storeId  # Fallback
                    print(f"💾 Store ID saved (fallback): {_store_id}")

        # Middleware: Kiểm tra login trước khi thực hiện các tasks khác
        if not check_login_required(driver, email, password, storeId, selected_tasks):
            return

        # Nếu chỉ chọn task login hoặc register, dừng tại đây
        if selected_tasks == ['login'] or selected_tasks == ['register_shopify_account']:
            print("\n✅ Task completed. No other tasks selected.")
        else:
            if 'install_apps' in selected_tasks:
                install_apps(driver, _store_id)

            if 'link_dser_account' in selected_tasks:
                link_dser_account(driver, password)

            if 'setup_world_market' in selected_tasks:
                setup_world_market(driver, _store_id)

            if 'setup_legal_policies' in selected_tasks:
                setup_legal_policies(driver, _store_id, {})

            if 'setup_contact_page' in selected_tasks:
                setup_contact_page(driver, _store_id)

            if 'setup_shipping_zones' in selected_tasks:
                setup_shipping_zones(driver, _store_id)

            if 'setup_preferences' in selected_tasks:
                setup_preferences(driver, _store_id)

            if 'connect_domain' in selected_tasks:
                await connect_domain(driver, _store_id, domain, get_config_json("cloudflare", "8", "token"))

            if 'setup_selleasy' in selected_tasks:
                setup_selleasy(driver, _store_id)

            if 'setup_content_menus' in selected_tasks:
                setup_content_menus(driver, _store_id)

            if 'import_themes' in selected_tasks:
                import_theme(driver, _store_id)

            if 'setup_notifications' in selected_tasks:
                await setup_notifications(driver, _store_id, domain, get_config_json("cloudflare", "8", "token"), get_config_json("cloudflare", "8", "email"), get_config_json("cloudflare", "8", "key"))
        try:
            cookies = driver.get_cookies()
            with open("cookies.pkl", "wb") as f:
                pickle.dump(cookies, f)
            print(f"Saved {len(cookies)} cookies")
        except Exception as e:
            print("Cookie save error:", e)

    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
    finally:
        stop_captcha_monitor()

        print("\n" + "="*80)
        print("✅ [Completed] All tasks have been completed.")
        print("📌 The browser will REMAIN OPEN for you to check the results.")
        print("🔴 Press Enter here when you WANT TO CLOSE the browser...")
        print("="*80)
        input()

        try:
            heartbeat.stop()
            driver.quit()
            print("✅ Browser has been closed successfully.")
        except:
            print("⚠️ Browser may have been closed manually.")

if __name__ == "__main__":
    asyncio.run(main())