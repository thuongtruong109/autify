from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element

def link_dser_account(driver: webdriver.Chrome, storeId: str, password: str):
    print("\n" + "="*60)
    print("🔄 XỬ LÝ MỞ VÀ XÁC NHẬN DSERS...")
    print("="*60)

    main_window_handle = driver.current_window_handle

    try:
        # 1. Mở tab mới với URL DSers app
        dser_app_url = "https://apps.shopify.com/dsers"
        print(f"📂 Mở tab mới với URL: {dser_app_url}")
        driver.execute_script(f"window.open('{dser_app_url}');")
        delay(3)

        new_tab_handle = None
        for handle in driver.window_handles:
            if handle != main_window_handle:
                new_tab_handle = handle
                break

        if not new_tab_handle:
            print("❌ Không tìm thấy tab mới. Bỏ qua.")
            return

        driver.switch_to.window(new_tab_handle)
        print("✅ Đã chuyển sang tab DSers app.")

        print("⏳ Đang chờ trang DSers app load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang DSers app đã load xong.")

        # 2. Tìm và click button "Open"
        print("🔍 Tìm button 'Open'...")
        open_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'open')] | //a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'open')]"))
        )

        highlight_element(driver, open_button)
        print(f"✅ Tìm thấy button 'Open'. Text: '{open_button.text}'. Click...")
        driver.execute_script("arguments[0].click();", open_button)
        delay(5)
        print("✅ Đã click button 'Open'.")

        # 3. Chờ tab mới mở ra (trang DSers chính)
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

        # 4. Chuyển sang tab DSers chính
        driver.switch_to.window(dser_main_tab)
        print(f"✅ Đã chuyển sang tab DSers chính: {driver.current_url}")

        print("⏳ Đang chờ trang DSers chính load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang DSers chính đã load xong.")

        # 5. Tìm và click button REGISTER YOURSELF
        register_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[@class='ant-btn ant-btn-hollowed REGISTER_YOURSELF']//span[text()='REGISTER YOURSELF']"))
        )

        print("🔍 Tìm thấy button 'REGISTER YOURSELF'. Click...")
        highlight_element(driver, register_button)
        driver.execute_script("arguments[0].click();", register_button)
        delay(3)
        print("✅ Đã click button 'REGISTER YOURSELF'.")

        print("⏳ Đang chờ trang load xong sau khi click REGISTER YOURSELF...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # 6. Điền password và click GET STARTED
        print("🔍 Tìm input password với id 'register_registerPs'...")
        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "register_registerPs"))
        )

        capitalized_password = password[0].upper() + password[1:] if len(password) > 0 else password

        highlight_element(driver, password_input)
        print(f"✅ Tìm thấy input password. Điền password (viết hoa ký tự đầu)...")
        password_input.clear()
        password_input.send_keys(capitalized_password)
        print("✅ Đã điền password.")

        # 7. Tìm và click button GET STARTED resgiter account
        print("🔍 Tìm button 'GET STARTED'...")
        get_started_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='ant-btn ant-btn-default ant-btn-lg Login_button__Hpdt-']//span[text()='GET STARTED']"))
        )

        highlight_element(driver, get_started_button)
        print(f"✅ Tìm thấy button 'GET STARTED'. Click...")
        driver.execute_script("arguments[0].click();", get_started_button)
        delay(3)
        print("✅ Đã click button 'GET STARTED'.")

        print("⏳ Đang chờ trang load xong sau khi click GET STARTED...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # 8. Tìm và click button 'confirm'
        print("🔍 Tìm button 'confirm'...")
        confirm_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='ant-btn ant-btn-primary footer_confirm']//span[text()='confirm']"))
        )

        highlight_element(driver, confirm_button)
        print(f"✅ Tìm thấy button 'confirm'. Click...")
        driver.execute_script("arguments[0].click();", confirm_button)
        delay(3)
        print("✅ Đã click button 'confirm'.")

        # 9. Tìm và click span 'GET STARTED' pricing page
        print("🔍 Tìm span với text 'GET STARTED'...")
        get_started_element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='GET STARTED']"))
        )

        highlight_element(driver, get_started_element)
        print(f"✅ Tìm thấy span 'GET STARTED'. Text: '{get_started_element.text}'. Click...")
        driver.execute_script("arguments[0].click();", get_started_element)
        delay(3)
        print("✅ Đã click span 'GET STARTED'.")

        # 10. Chờ trang redirect đến select/supply_apps
        print("⏳ Đang chờ trang redirect đến select/supply_apps...")
        WebDriverWait(driver, 30).until(
            lambda d: 'dsers.com/application/select/supply_apps' in d.current_url
        )
        print("✅ Đã redirect đến select/supply_apps page.")

        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang select/supply_apps đã load xong.")

        # 11. Tìm và click 'Link and authorize to AliExpress'
        print("🔍 Tìm div 'Link and authorize to AliExpress'...")
        aliexpress_link = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='CardSelect_cardLabel__oZmiX' and contains(text(), 'Link and authorize to AliExpress')]"))
        )

        highlight_element(driver, aliexpress_link)
        print(f"✅ Tìm thấy div 'Link and authorize to AliExpress'. Text: '{aliexpress_link.text}'. Click...")
        driver.execute_script("arguments[0].click();", aliexpress_link)
        delay(3)
        print("✅ Đã click div 'Link and authorize to AliExpress'.")

        print("⏳ Đang chờ trang load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang đã load xong.")

        # 12. Click Login to AliExpress
        print("🔍 Tìm button 'Login to AliExpress'...")
        login_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='ant-btn ant-btn-primary' and span[text()='LOGIN']]"))
        )

        highlight_element(driver, login_button)
        print(f"✅ Tìm thấy button 'LOGIN'. Click...")
        driver.execute_script("arguments[0].click();", login_button)
        delay(3)
        print("✅ Đã click button 'LOGIN'.")

        print("⏳ Đang chờ trang load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang đã load xong.")

        # 13. Click Authorize
        print("🔍 Tìm button 'Authorize'...")

        try:
            page_html = driver.page_source
            if 'authorize' in page_html.lower():
                print("✅ Tìm thấy từ 'authorize' trong HTML")
                # Tìm tất cả các button có chứa authorize
                buttons_with_authorize = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'authorize')]")
                print(f"📊 Số lượng button chứa 'authorize': {len(buttons_with_authorize)}")
                for idx, btn in enumerate(buttons_with_authorize):
                    print(f"  Button {idx + 1}: id='{btn.get_attribute('id')}', class='{btn.get_attribute('class')}', text='{btn.text}'")
            else:
                print("⚠️ KHÔNG tìm thấy từ 'authorize' trong HTML")

            # Kiểm tra button có id='sub'
            try:
                sub_button = driver.find_element(By.ID, "sub")
                print(f"✅ Tìm thấy button với id='sub': text='{sub_button.text}', onclick='{sub_button.get_attribute('onclick')}'")
            except:
                print("❌ KHÔNG tìm thấy button với id='sub'")

        except Exception as debug_error:
            print(f"⚠️ Lỗi khi debug: {debug_error}")

        # Thử nhiều cách tìm button Authorize
        authorize_button = None
        try:
            # Cách 1: Tìm theo ID
            print("🔍 Thử tìm theo ID='sub'...")
            authorize_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "sub"))
            )
            print("✅ Tìm thấy button Authorize theo ID!")
        except:
            print("❌ Không tìm thấy theo ID='sub'")

        if not authorize_button:
            try:
                # Cách 2: Tìm theo text chứa "Authorize"
                print("🔍 Thử tìm theo text chứa 'Authorize'...")
                authorize_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Authorize')]"))
                )
                print("✅ Tìm thấy button Authorize theo text!")
            except:
                print("❌ Không tìm thấy theo text 'Authorize'")

        if not authorize_button:
            try:
                # Cách 3: Tìm theo onclick attribute
                print("🔍 Thử tìm theo onclick='auther'...")
                authorize_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'auther')]"))
                )
                print("✅ Tìm thấy button Authorize theo onclick!")
            except:
                print("❌ Không tìm thấy theo onclick='auther'")

        if authorize_button:
            highlight_element(driver, authorize_button)
            print(f"✅ Tìm thấy button 'Authorize'. Click...")
            driver.execute_script("arguments[0].click();", authorize_button)
            delay(3)
            print("✅ Đã click button 'Authorize'.")

            print("⏳ Đang chờ trang load xong...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang đã load xong.")
        else:
            print("❌ KHÔNG TÌM THẤY button 'Authorize' bằng bất kỳ cách nào!")
            print("🔍 In ra current URL để kiểm tra:")
            print(f"   URL hiện tại: {driver.current_url}")

        print("\n✅ HOÀN TẤT XỬ LÝ MỞ VÀ XÁC NHẬN DSERS!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi xử lý mở và xác nhận DSers: {e}")
        print("="*60)
    finally:
        # print("🔄 Đóng các tab phụ và quay về main window...")
        # for handle in driver.window_handles:
        #     if handle != main_window_handle:
        #         try:
        #             driver.switch_to.window(handle)
        #             current_url = driver.current_url
        #             if 'dsers.com' not in current_url:
        #                 driver.close()
        #         except:
        #             pass
        # driver.switch_to.window(main_window_handle)
        print("✅ Đã quay về main window.")