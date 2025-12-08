import inquirer
import pickle
import asyncio

from configs.driver import setup_driver
from configs.anti_freeze import AntiFreeze

from utils.app import load_credentials
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
        ('setup_world_market', '🌍 Markets'),
        ('setup_legal_policies', '📜 Policies'),
        ('setup_contact_page', '📄 Pages'),
        ('setup_shipping_zones', '🚚 Shipping'),
        ('setup_preferences', '⚙️  Preferences'),
        ('connect_domain', '🌐 Domain'),
        ('setup_selleasy', '🎯 Selleasy'),
        ('setup_content_menus', '📋 Content Menus'),
        ('import_themes', '🎨 Import Themes'),
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
    # Nếu muốn dùng configs/config.json, đổi use_sheet=False
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

    heartbeat = AntiFreeze(driver, interval=15)
    heartbeat.start()

    start_captcha_monitor(driver, check_interval=2.0)

    cloudflare_token = "D0LRG-crTGRTqMn9udddaRCkzfw919PON0e2YpcP"

    try:
        if 'register_shopify_account' in selected_tasks:
                registered = register_shopify_account(driver, email, password, storeId, name, info)
                if not registered:
                    print("🚫 Registration failed. Cannot proceed.")
                    return
                print(f"\n✅ Registration successful for {name}!")
                print("="*60)

        if 'login' in selected_tasks or len(selected_tasks) > 0:
            print("\n🔐 Login to Shopify...")
            print("="*60)
            logged = login_to_shopify(driver, email, password, storeId)

            if not logged:
                print("🚫 Cannot proceed. Login failed.")
                return

            print("\n✅ Login successful!")
            print("="*60)

        if selected_tasks == ['login']:
            print("\n✅ Login completed. No other tasks selected.")
        else:
            if 'install_apps' in selected_tasks:
                install_apps(driver, storeId)

            if 'link_dser_account' in selected_tasks:
                link_dser_account(driver, storeId, password)

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

            if 'connect_domain' in selected_tasks:
                await connect_domain(driver, storeId, domain, cloudflare_token)

            if 'setup_selleasy' in selected_tasks:
                setup_selleasy(driver, storeId)

            if 'setup_content_menus' in selected_tasks:
                setup_content_menus(driver, storeId)

            if 'import_themes' in selected_tasks:
                import_theme(driver, storeId)

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