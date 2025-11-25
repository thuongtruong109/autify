from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element


def handle_dser_open_and_confirm(driver: webdriver.Chrome, storeId: str, password: str):
    """
    Mở tab mới đến trang DSers app, click "Open" button, sau đó trong tab mới click "CONFIRM" button.
    """
    print("\n" + "="*60)
    print("🔄 XỬ LÝ MỞ VÀ XÁC NHẬN DSERS...")
    print("="*60)

    main_window_handle = driver.current_window_handle

    try:
        # Bước 1: Mở tab mới với URL DSers app
        dser_app_url = "https://apps.shopify.com/dsers"
        print(f"📂 Mở tab mới với URL: {dser_app_url}")
        driver.execute_script(f"window.open('{dser_app_url}');")
        delay(3)

        # Tìm handle của tab mới
        new_tab_handle = None
        for handle in driver.window_handles:
            if handle != main_window_handle:
                new_tab_handle = handle
                break

        if not new_tab_handle:
            print("❌ Không tìm thấy tab mới. Bỏ qua.")
            return

        # Chuyển sang tab mới
        driver.switch_to.window(new_tab_handle)
        print("✅ Đã chuyển sang tab DSers app.")

        # Chờ page load xong
        print("⏳ Đang chờ trang DSers app load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang DSers app đã load xong.")

        # Bước 2: Tìm và click button "Open"
        print("🔍 Tìm button 'Open'...")
        open_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'open')] | //a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'open')]"))
        )

        highlight_element(driver, open_button)
        print(f"✅ Tìm thấy button 'Open'. Text: '{open_button.text}'. Click...")
        driver.execute_script("arguments[0].click();", open_button)
        delay(5)
        print("✅ Đã click button 'Open'.")

        # Bước 3: Chờ tab mới mở ra (trang DSers chính)
        print("⏳ Đang chờ tab mới mở ra...")
        dser_main_tab = None
        for attempt in range(10):
            current_handles = driver.window_handles
            if len(current_handles) > 2:  # main + app + dser main
                for handle in current_handles:
                    if handle != main_window_handle and handle != new_tab_handle:
                        dser_main_tab = handle
                        break
                if dser_main_tab:
                    break
            delay(1)

        if not dser_main_tab:
            print("⚠️ Không phát hiện tab mới mở ra. Có thể đã redirect trong cùng tab.")
            # Kiểm tra xem có redirect không
            current_url = driver.current_url
            if 'dsers.com' in current_url:
                print(f"ℹ️ Đã redirect đến: {current_url}")
                dser_main_tab = new_tab_handle
            else:
                print("❌ Không tìm thấy tab DSers chính.")
                return

        # Chuyển sang tab DSers chính
        driver.switch_to.window(dser_main_tab)
        print(f"✅ Đã chuyển sang tab DSers chính: {driver.current_url}")

        # Chờ page load xong
        print("⏳ Đang chờ trang DSers chính load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang DSers chính đã load xong.")

        # Flow xử lý theo URL hiện tại - kiểm tra liên tục sau mỗi bước

        # Bước 1: Kiểm tra nếu đang ở pricing page
        current_url = driver.current_url
        if 'dsers.com/application/pricing' in current_url:
            print("ℹ️ Đã ở pricing page, tiến hành click GET STARTED.")
            # Tìm và click span 'GET STARTED'
            print("🔍 Tìm span với text 'GET STARTED'...")
            get_started_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='GET STARTED']"))
            )

            highlight_element(driver, get_started_element)
            print(f"✅ Tìm thấy span 'GET STARTED'. Text: '{get_started_element.text}'. Click...")
            driver.execute_script("arguments[0].click();", get_started_element)
            delay(3)
            print("✅ Đã click span 'GET STARTED'.")

            # Chờ trang redirect đến select/supply_apps
            print("⏳ Đang chờ trang redirect đến select/supply_apps...")
            WebDriverWait(driver, 30).until(
                lambda d: 'dsers.com/application/select/supply_apps' in d.current_url
            )
            print("✅ Đã redirect đến select/supply_apps page.")

            # Chờ page load xong
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang select/supply_apps đã load xong.")

        # Bước 2: Kiểm tra lại URL - nếu đang ở select/supply_apps
        current_url = driver.current_url
        if 'dsers.com/application/select/supply_apps' in current_url:
            print("ℹ️ Đang ở select/supply_apps page, tiến hành click img.")
            # Tìm và click img trong div CardSelect_cardItemContainer__ZIPS5
            print("🔍 Tìm img trong div 'CardSelect_cardItemContainer__ZIPS5'...")
            img_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='CardSelect_cardItemContainer__ZIPS5']//img"))
            )

            highlight_element(driver, img_element)
            print(f"✅ Tìm thấy img. Alt: '{img_element.get_attribute('alt')}'. Click...")
            driver.execute_script("arguments[0].click();", img_element)
            delay(3)
            print("✅ Đã click img trong CardSelect_cardItemContainer.")

            # Chờ page load xong sau khi click
            print("⏳ Đang chờ trang load xong...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang đã load xong.")

        # Bước 3: Kiểm tra lại URL - nếu có pricing page với OAuthor
        current_url = driver.current_url
        if 'dsers.com/application/pricing' in current_url:
            print("ℹ️ Đang ở pricing page, tiến hành OAuthor với AliExpress.")

            # Tìm và click div 'Link and authorize to AliExpress'
            print("🔍 Tìm div 'Link and authorize to AliExpress'...")
            aliexpress_link = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='CardSelect_cardLabel__oZmiX' and contains(text(), 'Link and authorize to AliExpress')]"))
            )

            highlight_element(driver, aliexpress_link)
            print(f"✅ Tìm thấy div 'Link and authorize to AliExpress'. Text: '{aliexpress_link.text}'. Click...")
            driver.execute_script("arguments[0].click();", aliexpress_link)
            delay(3)
            print("✅ Đã click div 'Link and authorize to AliExpress'.")

            # Chờ page load xong sau khi click
            print("⏳ Đang chờ trang load xong...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang đã load xong.")

        # Bước 4: Kiểm tra nếu có button REGISTER YOURSELF
        current_url = driver.current_url
        try:
            register_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[@class='ant-btn ant-btn-hollowed REGISTER_YOURSELF']//span[text()='REGISTER YOURSELF']"))
            )

            print("🔍 Tìm thấy button 'REGISTER YOURSELF'. Click...")
            highlight_element(driver, register_button)
            driver.execute_script("arguments[0].click();", register_button)
            delay(3)
            print("✅ Đã click button 'REGISTER YOURSELF'.")

            # Chờ page load xong sau khi click
            print("⏳ Đang chờ trang load xong sau khi click REGISTER YOURSELF...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang đã load xong.")

            # Bước 5: Điền password và click GET STARTED
            print("🔍 Tìm input password với id 'register_registerPs'...")
            password_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "register_registerPs"))
            )

            # Viết hoa ký tự đầu tiên của password
            capitalized_password = password[0].upper() + password[1:] if len(password) > 0 else password

            highlight_element(driver, password_input)
            print(f"✅ Tìm thấy input password. Điền password (viết hoa ký tự đầu)...")
            password_input.clear()
            password_input.send_keys(capitalized_password)
            delay(2)
            print("✅ Đã điền password.")

            # Bước 6: Tìm và click button GET STARTED
            print("🔍 Tìm button 'GET STARTED'...")
            get_started_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='ant-btn ant-btn-default ant-btn-lg Login_button__Hpdt-']//span[text()='GET STARTED']"))
            )

            highlight_element(driver, get_started_button)
            print(f"✅ Tìm thấy button 'GET STARTED'. Click...")
            driver.execute_script("arguments[0].click();", get_started_button)
            delay(3)
            print("✅ Đã click button 'GET STARTED'.")

            # Chờ page load xong sau khi click GET STARTED
            print("⏳ Đang chờ trang load xong sau khi click GET STARTED...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang đã load xong.")

            # Bước 7: Tìm và click button 'confirm'
            print("🔍 Tìm button 'confirm'...")
            confirm_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='ant-btn ant-btn-primary footer_confirm']//span[text()='confirm']"))
            )

            highlight_element(driver, confirm_button)
            print(f"✅ Tìm thấy button 'confirm'. Click...")
            driver.execute_script("arguments[0].click();", confirm_button)
            delay(3)
            print("✅ Đã click button 'confirm'.")
        except:
            print("ℹ️ Không tìm thấy button 'REGISTER YOURSELF', bỏ qua bước này.")

        print("\n✅ HOÀN TẤT XỬ LÝ MỞ VÀ XÁC NHẬN DSERS!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi xử lý mở và xác nhận DSers: {e}")
        print("="*60)
    finally:
        # Đóng các tab phụ và quay về main, nhưng giữ tab DSers mở
        print("🔄 Đóng các tab phụ và quay về main window...")
        for handle in driver.window_handles:
            if handle != main_window_handle:
                try:
                    driver.switch_to.window(handle)
                    current_url = driver.current_url
                    if 'dsers.com' not in current_url:
                        driver.close()
                except:
                    pass
        driver.switch_to.window(main_window_handle)
        print("✅ Đã quay về main window.")