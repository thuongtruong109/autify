from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element, click_save_button

def setup_content_menus(driver: webdriver.Chrome, storeId: str):
    print("\n" + "="*60)
    print("🚚 SETUP CONTENT MENUS...")
    print("="*60)

    try:
        content_menus_url = f"https://admin.shopify.com/store/{storeId}/content/menus"
        print(f"Đang vào trang: {content_menus_url}")
        driver.get(content_menus_url)

        # 1. Đợi trang load và click vào Main menu link
        print("Đang đợi trang load và tìm link 'Main menu'...")
        wait = WebDriverWait(driver, 10)
        main_menu_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-primary-link='true' and contains(@href, '/content/menus/')]"))
        )
        highlight_element(driver, main_menu_link)
        print("Đã tìm thấy link 'Main menu', đang click...")
        main_menu_link.click()
        delay(1)
        print("✓ Đã click vào 'Main menu' thành công")

        # 2. Lặp lại việc tìm và xóa cho đến khi không còn button Delete nào
        while True:
            try:
                # 2.1 Tìm lại các button Delete (vì DOM thay đổi sau mỗi lần xóa)
                delete_buttons = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//button[starts-with(@aria-label, 'Delete')]"))
                )

                if not delete_buttons:
                    print("✓ Không còn button Delete nào")
                    break

                print(f"Đã tìm thấy {len(delete_buttons)} button(s) 'Delete'")

                # 2.2 Click vào button Delete đầu tiên
                delete_btn = delete_buttons[0]
                highlight_element(driver, delete_btn)
                aria_label = delete_btn.get_attribute("aria-label")
                print(f"Đang click button Delete: {aria_label}...")
                driver.execute_script("arguments[0].click();", delete_btn)
                delay(1)
                print(f"✓ Đã click '{aria_label}' thành công")

                # 2.3 Đợi modal xuất hiện và click button "Remove"
                print("Đang đợi modal và button 'Remove' xuất hiện...")
                remove_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'Polaris-Button') and contains(@class, 'toneCritical')]//span[contains(text(), 'Remove')]"))
                )
                highlight_element(driver, remove_button)
                print("Đã tìm thấy button 'Remove' trong modal, đang click...")
                driver.execute_script("arguments[0].click();", remove_button)
                print("✓ Đã click button 'Remove' thành công")

            except Exception as e:
                print(f"⚠️ Lỗi hoặc không còn button Delete: {e}")
                break

        # 3.1 Tìm và click button "Add menu item"
        print("Đang tìm button 'Add menu item'...")
        add_menu_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add menu item')]"))
        )
        highlight_element(driver, add_menu_button)
        print("Đã tìm thấy button 'Add menu item', đang click...")
        driver.execute_script("arguments[0].click();", add_menu_button)
        delay(1)
        print("✓ Đã click 'Add menu item' thành công")

        # 3.2 Tìm và click vào input search để mở dropdown menu
        print("Đang tìm input 'Search or paste link'...")
        search_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search or paste link']"))
        )
        highlight_element(driver, search_input)
        print("Đã tìm thấy input, đang click để focus và mở dropdown menu...")
        search_input.click()
        delay(1.5)
        print("✓ Đã click vào input, dropdown menu đang mở...")

        # 3.3 Đợi dropdown menu mở ra và click vào option "Home page"
        print("Đang đợi dropdown menu mở và tìm option 'Home page'...")
        delay(1)
        home_page_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'Home page')]]"))
        )
        highlight_element(driver, home_page_option)
        print("Đã tìm thấy option 'Home page' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", home_page_option)
        delay(1)
        print("✓ Đã click 'Home page' thành công")

        # 3.4 Tìm và click button "Close menu item"
        print("Đang tìm button 'Close menu item'...")
        close_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close menu item' and contains(@class, 'Polaris-Button--iconOnly')]"))
        )
        highlight_element(driver, close_button)
        print("Đã tìm thấy button 'Close menu item', đang click...")
        driver.execute_script("arguments[0].click();", close_button)
        delay(1)
        print("✓ Đã click 'Close menu item' thành công")

        # 4.1 Tìm và click button "Add menu item" lần 2
        print("\n[Thêm Products menu]")
        print("Đang tìm button 'Add menu item' lần 2...")
        add_menu_button_2 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add menu item')]"))
        )
        highlight_element(driver, add_menu_button_2)
        print("Đã tìm thấy button 'Add menu item', đang click...")
        driver.execute_script("arguments[0].click();", add_menu_button_2)
        delay(1)
        print("✓ Đã click 'Add menu item' thành công")

        # 4.2 Tìm và click vào input search lần 2 để mở dropdown menu
        print("Đang tìm input 'Search or paste link'...")
        search_input_2 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search or paste link']"))
        )
        highlight_element(driver, search_input_2)
        print("Đã tìm thấy input, đang click để focus và mở dropdown menu...")
        search_input_2.click()
        delay(1.5)
        print("✓ Đã click vào input, dropdown menu đang mở...")

        # 4.3 Đợi dropdown menu mở ra, tìm và click vào option "Products"
        print("Đang đợi dropdown menu mở và tìm option 'Products'...")
        delay(1)
        products_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'Products')]]"))
        )
        highlight_element(driver, products_option)
        print("Đã tìm thấy option 'Products' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", products_option)
        delay(1.5)
        print("✓ Đã click 'Products', đang load sub-options...")

        # Đợi sub-options load và tìm "All products" trong dropdown
        print("Đang đợi sub-options load và tìm 'All products'...")
        all_products_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'All products')]]"))
        )
        highlight_element(driver, all_products_option)
        print("Đã tìm thấy option 'All products' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", all_products_option)
        delay(1)
        print("✓ Đã click 'All products' thành công")

        # 4.4 Tìm và click button "Close menu item" lần 2
        print("Đang tìm button 'Close menu item' lần 2...")
        close_button_2 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close menu item' and contains(@class, 'Polaris-Button--iconOnly')]"))
        )
        highlight_element(driver, close_button_2)
        print("Đã tìm thấy button 'Close menu item', đang click...")
        driver.execute_script("arguments[0].click();", close_button_2)
        delay(1)
        print("✓ Đã click 'Close menu item' thành công")

        # 6.1 Tìm và click button "Add menu item" lần 3
        print("\n[Thêm Orders menu]")
        print("Đang tìm button 'Add menu item' lần 3...")
        add_menu_button_3 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add menu item')]"))
        )
        highlight_element(driver, add_menu_button_3)
        print("Đã tìm thấy button 'Add menu item', đang click...")
        driver.execute_script("arguments[0].click();", add_menu_button_3)
        delay(1)
        print("✓ Đã click 'Add menu item' thành công")

        # 6.2 Tìm và click vào input search lần 3 để mở dropdown menu
        print("Đang tìm input 'Search or paste link'...")
        search_input_3 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search or paste link']"))
        )
        highlight_element(driver, search_input_3)
        print("Đã tìm thấy input, đang click để focus và mở dropdown menu...")
        search_input_3.click()
        delay(1.5)
        print("✓ Đã click vào input, dropdown menu đang mở...")

        # 6.3 Đợi dropdown menu mở ra, tìm và click vào option "Orders"
        print("Đang đợi dropdown menu mở và tìm option 'Orders'...")
        delay(1)
        orders_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'Orders')]]"))
        )
        highlight_element(driver, orders_option)
        print("Đã tìm thấy option 'Orders' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", orders_option)
        delay(1)
        print("✓ Đã click 'Orders' thành công")

        # 6.4 Tìm và click button "Close menu item" lần 3
        print("Đang tìm button 'Close menu item' lần 3...")
        close_button_3 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close menu item' and contains(@class, 'Polaris-Button--iconOnly')]"))
        )
        highlight_element(driver, close_button_3)
        print("Đã tìm thấy button 'Close menu item', đang click...")
        driver.execute_script("arguments[0].click();", close_button_3)
        delay(1)
        print("✓ Đã click 'Close menu item' thành công")

        # 7.1 Tìm và click button "Add menu item" lần 4
        print("\n[Thêm About Us page menu]")
        print("Đang tìm button 'Add menu item' lần 4...")
        add_menu_button_4 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add menu item')]"))
        )
        highlight_element(driver, add_menu_button_4)
        print("Đã tìm thấy button 'Add menu item', đang click...")
        driver.execute_script("arguments[0].click();", add_menu_button_4)
        delay(1)
        print("✓ Đã click 'Add menu item' thành công")

        # 7.2 Tìm và click vào input search lần 4 để mở dropdown menu
        print("Đang tìm input 'Search or paste link'...")
        search_input_4 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search or paste link']"))
        )
        highlight_element(driver, search_input_4)
        print("Đã tìm thấy input, đang click để focus và mở dropdown menu...")
        search_input_4.click()
        delay(1.5)
        print("✓ Đã click vào input, dropdown menu đang mở...")

        # 7.3 Đợi dropdown menu mở ra, tìm và click vào option "Pages", sau đó chọn "About Us"
        print("Đang đợi dropdown menu mở và tìm option 'Pages'...")
        delay(1)
        pages_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'Pages')]]"))
        )
        highlight_element(driver, pages_option)
        print("Đã tìm thấy option 'Pages' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", pages_option)
        delay(1.5)
        print("✓ Đã click 'Pages', đang load sub-options...")

        # Đợi sub-options load và tìm "About Us" trong dropdown
        print("Đang đợi sub-options load và tìm 'About Us'...")
        about_us_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'About Us')]]"))
        )
        highlight_element(driver, about_us_option)
        print("Đã tìm thấy option 'About Us' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", about_us_option)
        delay(1)
        print("✓ Đã click 'About Us' thành công")

        # 7.4 Tìm và click button "Close menu item" lần 4
        print("Đang tìm button 'Close menu item' lần 4...")
        close_button_4 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close menu item' and contains(@class, 'Polaris-Button--iconOnly')]"))
        )
        highlight_element(driver, close_button_4)
        print("Đã tìm thấy button 'Close menu item', đang click...")
        driver.execute_script("arguments[0].click();", close_button_4)
        delay(1)
        print("✓ Đã click 'Close menu item' thành công")

        # 8.1 Tìm và click button "Add menu item" lần 5
        print("\n[Thêm Contact page menu]")
        print("Đang tìm button 'Add menu item' lần 5...")
        add_menu_button_5 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add menu item')]"))
        )
        highlight_element(driver, add_menu_button_5)
        print("Đã tìm thấy button 'Add menu item', đang click...")
        driver.execute_script("arguments[0].click();", add_menu_button_5)
        delay(1)
        print("✓ Đã click 'Add menu item' thành công")

        # 8.2 Tìm và click vào input search lần 5 để mở dropdown menu
        print("Đang tìm input 'Search or paste link'...")
        search_input_5 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search or paste link']"))
        )
        highlight_element(driver, search_input_5)
        print("Đã tìm thấy input, đang click để focus và mở dropdown menu...")
        search_input_5.click()
        delay(1.5)
        print("✓ Đã click vào input, dropdown menu đang mở...")

        # 8.3 Đợi dropdown menu mở ra, tìm và click vào option "Pages", sau đó chọn "Contact"
        print("Đang đợi dropdown menu mở và tìm option 'Pages'...")
        delay(1)
        pages_option_2 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'Pages')]]"))
        )
        highlight_element(driver, pages_option_2)
        print("Đã tìm thấy option 'Pages' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", pages_option_2)
        delay(1.5)
        print("✓ Đã click 'Pages', đang load sub-options...")

        # Đợi sub-options load và tìm "Contact" trong dropdown
        print("Đang đợi sub-options load và tìm 'Contact'...")
        contact_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@role='list']//button[.//div[contains(text(), 'Contact')]]"))
        )
        highlight_element(driver, contact_option)
        print("Đã tìm thấy option 'Contact' trong dropdown, đang click...")
        driver.execute_script("arguments[0].click();", contact_option)
        delay(1)
        print("✓ Đã click 'Contact' thành công")

        # 8.4 Tìm và click button "Close menu item" lần 5
        print("Đang tìm button 'Close menu item' lần 5...")
        close_button_5 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close menu item' and contains(@class, 'Polaris-Button--iconOnly')]"))
        )
        highlight_element(driver, close_button_5)
        print("Đã tìm thấy button 'Close menu item', đang click...")
        driver.execute_script("arguments[0].click();", close_button_5)
        delay(1)
        print("✓ Đã click 'Close menu item' thành công")

        click_save_button(driver)

    except Exception as e:
        print(f"❌ Lỗi khi setup content menus: {e}")
        driver.switch_to.default_content()