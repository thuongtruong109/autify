from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element


def handle_dser_open_and_confirm(driver: webdriver.Chrome, storeId: str):
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

        # Kiểm tra URL hiện tại
        current_url = driver.current_url
        if 'dsers.com/application/select/supply_apps' in current_url:
            print("ℹ️ Đã ở select/supply_apps page, tiến hành click img.")
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
        elif 'dsers.com/application/pricing' in current_url:
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

            # Chờ trang redirect đến select/supply_apps và click img
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
        else:
            # Bước 4: Tìm và click span với text 'confirm'
            print("🔍 Tìm span với text 'confirm'...")
            confirm_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='confirm']"))
            )

            highlight_element(driver, confirm_element)
            print(f"✅ Tìm thấy span 'confirm'. Text: '{confirm_element.text}'. Click...")
            driver.execute_script("arguments[0].click();", confirm_element)
            delay(3)
            print("✅ Đã click span 'confirm'.")

            # Bước 5: Chờ trang redirect đến pricing page và click 'GET STARTED'
            print("⏳ Đang chờ trang redirect đến pricing page...")
            WebDriverWait(driver, 30).until(
                lambda d: 'dsers.com/application/pricing' in d.current_url
            )
            print("✅ Đã redirect đến pricing page.")

            # Chờ page load xong
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Trang pricing đã load xong.")

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

            # Bước 6: Chờ trang redirect đến select/supply_apps và click img
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