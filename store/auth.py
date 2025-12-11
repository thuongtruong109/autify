import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, wait_for_admin, find_button, highlight_element

"""
CAPTCHA AUTO-HANDLING ARCHITECTURE
===================================

BACKGROUND THREAD (Captcha Monitor):
    └─> Liên tục check captcha mỗi 2s (silent)
    └─> KHI PHÁT HIỆN CAPTCHA:
        1. Lock để tránh xử lý trùng
        2. Can thiệp vào driver để xử lý captcha
        3. Retry đến khi captcha được giải quyết
        4. Release lock và tiếp tục monitor

MAIN THREAD (Login/Tasks):
    └─> Chạy logic bình thường
    └─> KHÔNG CẦN gọi bất kỳ wait/check function nào
    └─> Viết code như không có captcha
    └─> Driver operations tự động đợi khi captcha đang được xử lý

FLOW DIAGRAM:
    Main Thread                    Background Thread
        |                                 |
        ├─ navigate(url)                  ├─ (check...) ✓ no captcha
        ├─ fill_email()                   ├─ (check...) ✓ no captcha
        ├─ click_button()                 ├─ (check...) ⚠️ CAPTCHA!
        |                                 ├─ 🔒 LOCK + handle captcha
        ├─ fill_password() ⏸️              |    (blocking monitor only)
        |    (đợi driver available)       ├─ captcha solving...
        |    (tự động - không code gì)    ├─ captcha solved! ✓
        ├─ ▶️ tiếp tục tự động             ├─ 🔓 UNLOCK
        ├─ click_login()                  ├─ (check...) ✓ no captcha
        └─ ...                            └─ ...

✅ MAIN THREAD CHẠY TỰ DO - KHÔNG CẦN QUAN TÂM CAPTCHA!
✅ MONITOR TỰ ĐỘNG XỬ LÝ - MỌI THỨ DIỄN RA TỰ NHIÊN!
✅ 2 LUỒNG ĐỘC LẬP - KHÔNG EXPLICIT PAUSE/RESUME!
"""

# Global state cho captcha monitor
_captcha_monitor_active = False
_captcha_monitor_thread = None
_captcha_being_handled = threading.Event()  # Signal: captcha đang được xử lý
_captcha_resolved = threading.Event()       # Signal: captcha đã được giải quyết
_captcha_lock = threading.Lock()            # Lock để tránh xử lý captcha trùng lặp

def login_to_shopify(driver: webdriver.Chrome, email: str, password: str, storeId: str) -> bool:
    # 1. Navigate to store admin URL
    login_url = f"https://admin.shopify.com/store/{storeId}"
    driver.get(login_url)
    delay(1)

    # 2. KIỂM TRA ĐĂNG NHẬP
    print("Checking login status...")
    logged = wait_for_admin(driver, 10)

    if logged:
        print("✅ Already logged in. Skipping login steps.")
        return True

    print("⚠️ Not logged in. Starting login process...")

    # Main thread chạy bình thường - KHÔNG đợi captcha cố định
    # Background thread sẽ tự động xử lý captcha khi phát hiện

    email_selectors = 'input[type="email"], input#account_email'
    try:
        # Đợi và điền email
        print("🔍 Đang tìm email input...")
        email_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, email_selectors)))
        email_el.clear()
        email_el.send_keys(email)
        print(f"✅ Đã điền email: {email}")
        delay(0.5)

        # ===== TÌM VÀ CLICK BUTTON 'CONTINUE WITH EMAIL' =====
        # Background thread sẽ tự động xử lý captcha nếu xuất hiện
        print("🔍 Đang tìm button 'Continue with email'...")
        keywords_lower = ["continue with email", "tiếp tục bằng email"]
        keyword_conditions = [
            f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k}')"
            for k in keywords_lower
        ]
        xpath_query = (
            f"//button[{' or '.join(keyword_conditions)}] | "
            f"//a[{' or '.join(keyword_conditions)}]"
        )

        # Đợi button visible và enabled, rồi click ngay
        print("⏳ Đang đợi button 'Continue with email' sẵn sàng...")
        cont_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath_query))
        )
        highlight_element(driver, cont_btn)
        print("✅ Button 'Continue with email' đã visible và enabled!")
        cont_btn.click()
        print("✅ Đã click button 'Continue with email'")
        delay(2)

    except Exception as e:
        print(f"⚠️ Lỗi khi xử lý email input hoặc click continue button: {e}")
        print("💡 Có thể cần xử lý captcha hoặc login thủ công")
        pass

    pass_selectors = 'input[type="password"], input#account_password'
    try:
        pass_el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, pass_selectors)))
        pass_el.clear()
        pass_el.send_keys(password)
        delay(0.5)

        login_btn = find_button(driver, ["Log in", "Đăng nhập"])
        if login_btn:
            login_btn.click()
    except Exception:
        pass

    # 3. Wait for Admin UI after login
    print("Solve CAPTCHA/2FA manually if needed...")
    logged = wait_for_admin(driver, 60)

    if not logged:
        print("\n" + "*"*80)
        input("Admin UI not detected. Please login manually in the browser. Press Enter here when complete...")
        print("*"*80 + "\n")
        # Kiểm tra lại sau khi user login thủ công
        logged = wait_for_admin(driver, 10)

    return logged

def register_shopify_account(driver: webdriver.Chrome, email: str, password: str, domain: str, name: str = "", info: str = "") -> bool:
    print(f"\n{'='*50}\nStarting Shopify registration process\n{'='*50}")
    if name:
        print(f"👤 Name: {name}")
    if info:
        print(f"📋 Info: {info}")

    # 1. Navigate to Shopify admin homepage
    signup_url = "https://www.shopify.com/"
    driver.get(signup_url)
    delay(2)

    # 2. Find and click "Start for free" button
    print("🔍 Tìm button 'Start for free'...")
    try:
        # Tìm button với text "Start for free" hoặc link có chứa /signup
        start_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start for free') or @data-component-name='start-free-trial']"
            ))
        )

        highlight_element(driver, start_button)
        print("✅ Tìm thấy button 'Start for free'. Click...")
        start_button.click()
        delay(3)

        # 3. Wait for new page to load
        print("⏳ Đợi trang đăng ký load...")
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        delay(2)

        # 5. Find and fill email input
        print("🔍 Tìm input email và điền thông tin...")
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]#account_email, input[name="account[email]"]'))
            )
            highlight_element(driver, email_input)
            email_input.click()
            delay(0.5)
            email_input.clear()
            email_input.send_keys(email)
            print(f"✅ Đã điền email: {email}")
            delay(1)

            # 6. Find and click "Continue with email" button
            print("🔍 Tìm và click button 'Continue with email'...")
            continue_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@class, 'login-button') and @type='submit']//span[contains(text(), 'Continue with email')]/.."
                ))
            )
            highlight_element(driver, continue_btn)
            continue_btn.click()
            print("✅ Đã click 'Continue with email'.")
            delay(3)

        except Exception as e:
            print(f"⚠️ Lỗi khi điền email hoặc click Continue: {e}")
            # Thử cách khác
            try:
                cont_btn = find_button(driver, ["Continue with email", "Continue"])
                if cont_btn:
                    highlight_element(driver, cont_btn)
                    cont_btn.click()
                    print("✅ Đã click 'Continue with email' (fallback).")
                    delay(3)
            except Exception as e2:
                print(f"⚠️ Không thể click Continue button: {e2}")

        # 7. Wait for password input and fill it
        print("🔍 Đợi input password xuất hiện...")
        try:
            password_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    'input#account_password, input[name="account[password]"], input[type="password"][autocomplete="new-password"]'
                ))
            )
            highlight_element(driver, password_input)
            password_input.click()
            delay(0.5)
            password_input.clear()
            password_input.send_keys(password)
            print(f"✅ Đã điền password.")
            delay(1)

        except Exception as e:
            print(f"⚠️ Lỗi khi điền password: {e}")

        # 8. Background monitor sẽ tự động xử lý captcha nếu có
        print("ℹ️  Background captcha monitor đang chạy - sẽ tự động xử lý 'I am human' nếu xuất hiện")
        print("⏳ Đợi một chút để monitor có thời gian xử lý...")
        delay(3)

        # 9. Wait for "Create Shopify account" button to be enabled and visible, then click
        print("🔍 Đang đợi button 'Create Shopify account' được enable và visible...")
        try:
            # Wait for the button to be present, enabled (no disabled attribute), and clickable
            create_account_btn = WebDriverWait(driver, 60).until(
                lambda d: d.find_element(By.XPATH, "//button[@type='submit' and @name='commit' and contains(@class, 'captcha__submit') and contains(., 'Create Shopify account')]")
                if not d.find_element(By.XPATH, "//button[@type='submit' and @name='commit' and contains(@class, 'captcha__submit') and contains(., 'Create Shopify account')]").get_attribute('disabled')
                else None
            )

            # Double check it's clickable
            create_account_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @name='commit' and contains(@class, 'captcha__submit') and contains(., 'Create Shopify account')]"))
            )

            highlight_element(driver, create_account_btn)
            print("✅ Button 'Create Shopify account' đã sẵn sàng, đang click ngay...")
            create_account_btn.click()
            print("✅ Đã click button 'Create Shopify account'.")
            delay(3)

        except Exception as e:
            print(f"⚠️ Lỗi khi đợi hoặc click button 'Create Shopify account': {e}")
            print("⚠️ Có thể cần xác minh thủ công.")

        print("\n" + "*"*80)
        print("✅ Đã hoàn thành các bước tự động. Vui lòng kiểm tra và hoàn thành các bước còn lại (nếu có).")
        input("Nhấn Enter khi đã hoàn thành đăng ký...")
        print("*"*80 + "\n")

        return True

    except Exception as e:
        print(f"❌ Lỗi trong quá trình đăng ký: {e}")
        print("\n" + "*"*80)
        input("Vui lòng hoàn thành đăng ký thủ công và nhấn Enter để tiếp tục...")
        print("*"*80 + "\n")
        return False

    # # 10. Add card info
    # setup_url = "https://admin.shopify.com/signup/38ec7dce-a620-4b94-991d-ba99758ddb12/checkout/extend-trial?locale=en&language=en&signup_page=https%3A%2F%2Fwww.shopify.com%2F&signup_types%5B%5D=paid_trial_experience&_y=8e5df360-2a32-49f6-bfb7-0a65e04750cd&_s=e6ff71a6-6b25-4ec0-ba91-6303b393ddf6&_p=9cafeb48-eeae-4916-906d-42b3055f0cec&country=VN&shopPermanentDomain=wuvx3q-0i.myshopify.com"

    # first_name, last_name = extract_fullname(name)
    # _, _, address, zip = extract_info(info)

    # # Navigate to setup URL and fill card info
    # print("🔍 Đang chuyển đến trang setup để thêm thông tin thẻ...")
    # driver.get(setup_url)
    # delay(2)

    # # Wait for page to load
    # WebDriverWait(driver, 15).until(
    #     lambda d: d.execute_script("return document.readyState") == "complete"
    # )
    # delay(1)

    # # Fill first name
    # print("🔍 Đang đợi input first name...")
    # first_name_input = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="firstName"]'))
    # )
    # highlight_element(driver, first_name_input)
    # first_name_input.click()
    # delay(0.5)
    # first_name_input.clear()
    # first_name_input.send_keys(first_name)
    # print(f"✅ Đã điền first name: {first_name}")

    # # Fill last name
    # print("🔍 Đang đợi input last name...")
    # last_name_input = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="lastName"]'))
    # )
    # highlight_element(driver, last_name_input)
    # last_name_input.click()
    # delay(0.5)
    # last_name_input.clear()
    # last_name_input.send_keys(last_name)
    # print(f"✅ Đã điền last name: {last_name}")

    # # Fill address
    # print("🔍 Đang đợi input address...")
    # address_input = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="address1"]'))
    # )
    # highlight_element(driver, address_input)
    # address_input.click()
    # delay(0.5)
    # address_input.clear()
    # address_input.send_keys(address)
    # print(f"✅ Đã điền address: {address}")

    # # Fill zip
    # print("🔍 Đang đợi input zip...")
    # zip_input = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="zip"]'))
    # )
    # highlight_element(driver, zip_input)
    # zip_input.click()
    # delay(0.5)
    # zip_input.clear()
    # zip_input.send_keys(zip)
    # print(f"✅ Đã điền zip: {zip}")

    # print("✅ Đã hoàn thành điền thông tin thẻ. Vui lòng kiểm tra và hoàn thành các bước còn lại.")