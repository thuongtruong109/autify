from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button
from typing import List, Tuple

def add_menu_item(driver: webdriver.Chrome, wait: WebDriverWait, menu_item_name: str, sub_option_name: str = None) -> bool:
    print(f"\n[Thêm Menu Item: {menu_item_name} -> {sub_option_name or 'None'}]")
    try:
        # 1. Tìm và click button "Add menu item"
        add_menu_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add menu item')]"))
        )
        highlight_element(driver, add_menu_button)
        driver.execute_script("arguments[0].click();", add_menu_button)
        delay(1)
        print("✓ Đã click 'Add menu item'")

        # 2. Tìm và click vào input search để mở dropdown menu
        search_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search or paste link']"))
        )
        highlight_element(driver, search_input)
        search_input.click()
        delay(1.5)
        print("✓ Đã click vào input search")

        # 3. Đợi dropdown menu mở ra và click vào option chính
        print(f"Đang tìm option chính: '{menu_item_name}'...")
        delay(1)

        # Xây dựng XPATH cho mục menu/tùy chọn
        def get_option_xpath(name):
            # Tìm button trong list có div chứa text chính xác
            return f"//ul[@role='list']//button[.//div[contains(text(), '{name}') and not(contains(text(), '{name}('))]]"

        main_option_xpath = get_option_xpath(menu_item_name)

        main_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, main_option_xpath))
        )
        highlight_element(driver, main_option)
        driver.execute_script("arguments[0].click();", main_option)
        delay(1.5)
        print(f"✓ Đã click '{menu_item_name}'")

        # 4. Nếu có sub-option, đợi sub-options load và click vào sub-option
        if sub_option_name:
            print(f"Đang tìm sub-option: '{sub_option_name}'...")
            sub_option_xpath = get_option_xpath(sub_option_name)

            sub_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, sub_option_xpath))
            )
            highlight_element(driver, sub_option)
            driver.execute_script("arguments[0].click();", sub_option)
            delay(1)
            print(f"✓ Đã click '{sub_option_name}'")

        # 5. Tìm và click button "Close menu item"
        print("Đang tìm và click button 'Close menu item'...")
        close_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close menu item' and contains(@class, 'Polaris-Button--iconOnly')]"))
        )
        highlight_element(driver, close_button)
        driver.execute_script("arguments[0].click();", close_button)
        delay(1)
        print("✓ Đã click 'Close menu item' thành công")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi thêm menu item '{menu_item_name}' -> '{sub_option_name or 'None'}': {e}")
        return False

def delete_all_menu_items(driver: webdriver.Chrome, wait: WebDriverWait):
    print("🗑️ Đang tiến hành xóa tất cả các mục menu cũ...")
    while True:
        try:
            # 1. Tìm lại các button Delete (vì DOM thay đổi sau mỗi lần xóa)
            # Dùng presence_of_all_elements_located để tìm tất cả các nút ngay khi chúng xuất hiện.
            delete_buttons = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[starts-with(@aria-label, 'Delete')]"))
            )

            if not delete_buttons:
                print("✓ Không còn mục menu để xóa.")
                break

            print(f"Đã tìm thấy {len(delete_buttons)} mục menu để xóa.")

            # 2. Click vào button Delete đầu tiên
            delete_btn = delete_buttons[0]
            highlight_element(driver, delete_btn)
            aria_label = delete_btn.get_attribute("aria-label")
            print(f"Đang click button Delete: {aria_label}...")
            driver.execute_script("arguments[0].click();", delete_btn)
            delay(1)

            # 3. Đợi modal xuất hiện và click button "Remove"
            remove_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'Polaris-Button') and contains(@class, 'toneCritical')]//span[contains(text(), 'Remove')]"))
            )
            highlight_element(driver, remove_button)
            driver.execute_script("arguments[0].click();", remove_button)
            delay(1)
            print(f"✓ Đã xóa '{aria_label}' thành công")

        except Exception as e:
            # Thường xảy ra TimeoutException khi không tìm thấy nút nào nữa
            print(f"⚠️ Hoàn tất quy trình xóa hoặc xảy ra lỗi: {e}")
            break

def setup_content_menus(driver: webdriver.Chrome, storeId: str):
    print("\n" + "="*60)
    print("🚚 SETUP CONTENT MENUS...")
    print("="*60)
    wait = WebDriverWait(driver, 10)

    main_menu_items: List[Tuple[str, str | None]] = [
        ("Home page", None),
        ("Products", "All products"),
        ("Orders", None),
        ("Pages", "About Us"),
        ("Pages", "Contact"),
    ]

    policies_menu_items: List[Tuple[str, str | None]] = [
        ("Policies", "Contact Information"),
        ("Policies", "Privacy Policy"),
        ("Policies", "Refund Policy"),
        ("Policies", "Shipping Policy"),
        ("Policies", "Terms of Service"),
    ]

    try:
        content_menus_url = f"https://admin.shopify.com/store/{storeId}/content/menus"
        print(f"➡️ Đang vào trang: {content_menus_url}")
        driver.get(content_menus_url)

        # 1. Đợi trang load và click vào Main menu link
        print("🔎 Đang đợi trang load và tìm link 'Main menu'...")
        main_menu_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-primary-link='true' and contains(@href, '/content/menus/')]"))
        )
        highlight_element(driver, main_menu_link)
        main_menu_link.click()
        delay(1)
        print("✓ Đã click vào 'Main menu'")

        # 2. Xóa các mục menu hiện có
        delete_all_menu_items(driver, wait)

        # 3. Thêm các mục menu mới
        print("\n➕ Bắt đầu thêm các mục menu chính...")
        for main_item, sub_item in main_menu_items:
            add_menu_item(driver, wait, main_item, sub_item)

        # 4. Lưu lại Main Menu (Giả định có click_save_button trong utils)
        print("💾 Đang lưu lại Main Menu...")
        click_save_button(driver)
        print("✓ Đã lưu Main Menu thành công")

    except Exception as e:
        print(f"❌ Lỗi khi setup content main menus: {e}")
        driver.switch_to.default_content()

    try:
        content_menus_url = f"https://admin.shopify.com/store/{storeId}/content/menus/new"
        print(f"\n➡️ Đang vào trang: {content_menus_url} để tạo menu mới (Policies)...")
        driver.get(content_menus_url)
        delay(2) # Đợi trang load

        # 1. **CẦN THÊM BƯỚC:** Nhập tên menu (vd: 'Footer Menu' hoặc 'Policies')
        print("📝 Đang nhập tên menu là 'Policies'...")
        menu_title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="title"][placeholder="e.g., Sidebar menu"]')))
        menu_title_input.click()
        menu_title_input.clear()
        menu_title_input.send_keys("Policies")
        delay(1)

        # 2. Thêm các mục Policies
        print("\n➕ Bắt đầu thêm các mục menu Policies...")
        for main_item, sub_item in policies_menu_items:
            add_menu_item(driver, wait, main_item, sub_item)

        # 3. Lưu lại Menu mới
        print("💾 Đang lưu lại Policies Menu...")
        click_save_button(driver)
        print("✓ Đã lưu Policies Menu thành công")

    except Exception as e:
        print(f"❌ Lỗi khi setup content policies menus: {e}")
        driver.switch_to.default_content()