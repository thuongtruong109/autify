import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, wait_for_admin, find_button, highlight_element
from libs.sheet import extract_fullname, extract_info

_captcha_monitor_active = False
_captcha_monitor_thread = None

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

    email_selectors = 'input[type="email"], input#account_email'
    try:
        email_el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, email_selectors)))
        email_el.clear()
        email_el.send_keys(email)
        print(f"✅ Đã điền email: {email}")
        delay(1)

        # ===== XỬ LÝ SONG SONG: CAPTCHA VÀ CHECK BUTTON =====
        print("🔍 Đang xử lý Shopify captcha và đồng thời check button 'Continue with email'...")

        keywords_lower = ["continue with email", "tiếp tục bằng email"]
        keyword_conditions = [
            f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k}')"
            for k in keywords_lower
        ]
        xpath_query = (
            f"//button[{' or '.join(keyword_conditions)}] | "
            f"//a[{' or '.join(keyword_conditions)}]"
        )

        max_wait_time = 30  # Tối đa 30 giây
        check_interval = 0.5  # Check mỗi 0.5 giây
        elapsed_time = 0
        button_clicked = False
        captcha_attempted = False

        while elapsed_time < max_wait_time and not button_clicked:
            try:
                # 1. Kiểm tra xem button đã visible và clickable chưa
                cont_buttons = driver.find_elements(By.XPATH, xpath_query)

                for btn in cont_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            # Button đã sẵn sàng → click ngay
                            highlight_element(driver, btn)
                            print("✅ Button 'Continue with email' đã sẵn sàng → Click ngay và bỏ qua captcha!")
                            btn.click()
                            button_clicked = True
                            delay(2)
                            break
                    except:
                        continue

                if button_clicked:
                    break

                # 2. Nếu button chưa sẵn sàng, thử xử lý captcha (chỉ làm 1 lần)
                if not captcha_attempted:
                    captcha_handled = shopify_captcha(driver, auto_solve=True, verbose=False)
                    if captcha_handled:
                        print("✅ Đã xử lý Shopify captcha. Đang đợi button sẵn sàng...")
                    captcha_attempted = True

                # 3. Chờ một chút trước khi check lại
                time.sleep(check_interval)
                elapsed_time += check_interval

            except Exception as e:
                # Tiếp tục loop nếu có lỗi
                time.sleep(check_interval)
                elapsed_time += check_interval
                continue

        if not button_clicked:
            # Fallback: Thử wait với WebDriverWait
            print("⚠️ Chưa click được button. Thử phương thức chờ thông thường...")
            try:
                cont_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_query))
                )
                highlight_element(driver, cont_btn)
                print("✅ Button 'Continue with email' đã sẵn sàng (fallback), đang click...")
                cont_btn.click()
                delay(2)
            except Exception as e:
                print(f"⚠️ Không thể click button 'Continue with email': {e}")
    except Exception as e:
        print(f"⚠️ Lỗi khi xử lý email input hoặc continue button: {e}")
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

def cloudflare_captcha(driver: webdriver.Chrome, verbose: bool = True) -> bool:
    """
    Xử lý Cloudflare captcha bằng cách tìm <h1> chứa text "Your connection needs to be verified"
    và thực hiện các thao tác click như trong test_cf_xpath.py
    """
    import random
    from selenium.webdriver.common.action_chains import ActionChains

    def find_h1_element(text_to_find):
        """Tìm <h1> chứa text, trả về element hoặc None."""
        try:
            return driver.find_element(By.XPATH, f"//h1[contains(text(), '{text_to_find}')]")
        except:
            return None

    def click_offset_with_marker(x, y):
        """Click vật lý tại (x,y) và tạo marker đỏ."""
        actions = ActionChains(driver)
        actions.move_by_offset(x, y).click().perform()
        actions.reset_actions()

        js_marker = f"""
        const marker = document.createElement('div');
        marker.style.position = 'absolute';
        marker.style.left = '{x-5}px';
        marker.style.top = '{y-5}px';
        marker.style.width = '10px';
        marker.style.height = '10px';
        marker.style.background='red';
        marker.style.borderRadius='50%';
        marker.style.zIndex='9999';
        document.body.appendChild(marker);
        """
        driver.execute_script(js_marker)

    try:
        # Check xem driver còn sống không
        try:
            _ = driver.current_url  # Test connection
        except Exception as e:
            if verbose:
                print(f"⚠️ Driver không khả dụng: {str(e)[:50]}")
            return False

        text_to_find = "Your connection needs to be verified"
        element = find_h1_element(text_to_find)

        if not element:
            if verbose:
                print("🔍 Không tìm thấy Cloudflare challenge element")
            return False

        if verbose:
            print(f"✅ Tìm thấy Cloudflare challenge element!")

        # Highlight element
        try:
            highlight_element(driver, element, "yellow")
        except:
            pass

        rect = element.rect
        base_x = rect['x'] + rect['width']/2
        base_y = rect['y'] + rect['height']/2

        # Cấu hình
        offset_x = -180
        offset_y = 60
        random_clicks = 6
        random_range = 25
        random_click_delay = (0.8, 1.5)

        # Random click nhiều lần
        for _ in range(random_clicks):
            rand_x = base_x + random.randint(-random_range, random_range)
            rand_y = base_y + random.randint(-random_range, random_range)
            click_offset_with_marker(rand_x, rand_y)
            if verbose:
                print(f"🎯 Random click tại ({rand_x:.0f},{rand_y:.0f}) với marker đỏ")
            time.sleep(random.uniform(*random_click_delay))

        # Click thật tại offset
        click_x = base_x + offset_x
        click_y = base_y + offset_y
        click_offset_with_marker(click_x, click_y)
        if verbose:
            print(f"🖱 Click thật tại ({click_x:.0f},{click_y:.0f}) với marker đỏ")
            print("✅ ĐÃ XỬ LÝ CLOUDFLARE CAPTCHA!")

        time.sleep(2)
        return True

    except Exception as e:
        if verbose:
            print(f"⚠️ Lỗi khi xử lý Cloudflare captcha: {e}")
        return False


def _captcha_monitor_background(driver: webdriver.Chrome, check_interval: float = 2.0):
    """
    Background thread để liên tục kiểm tra và xử lý cả Cloudflare captcha và Shopify captcha SONG SONG.

    Thread này chạy GLOBAL trong suốt lifecycle của driver, không chỉ trong login.
    Nó sẽ tự động detect và xử lý captcha ở bất kỳ page nào trong quá trình automation.
    """
    global _captcha_monitor_active

    print("\n" + "="*70)
    print("🔄 CAPTCHA MONITOR ĐÃ BẮT ĐẦU (chạy trong background)")
    print("   🔍 Đang theo dõi: Cloudflare Captcha + Shopify Captcha")
    print(f"   ⏱️  Check interval: {check_interval}s")
    print(f"   🎯 Trạng thái: ĐANG CHẠY GLOBAL (cho mọi task)")
    print("="*70 + "\n")

    check_count = 0
    consecutive_errors = 0
    max_consecutive_errors = 5

    while _captcha_monitor_active:
        check_count += 1

        # Log mỗi 10 lần check để người dùng biết monitor vẫn đang chạy
        if check_count % 10 == 1:
            print(f"🔍 [Monitor] Đang check captcha lần thứ #{check_count}...")

        try:
            # 🔍 KIỂM TRA DRIVER CÒN SỐNG KHÔNG (tránh HTTPConnectionPool error)
            try:
                _ = driver.current_url
                consecutive_errors = 0  # Reset error counter nếu driver OK
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\n⚠️ [Monitor] Driver không còn khả dụng sau {max_consecutive_errors} lần thử.")
                    print("⚠️ [Monitor] Dừng monitor để tránh spam errors.")
                    break
                # Skip iteration này nếu driver chết
                time.sleep(check_interval)
                continue

            # XỬ LÝ SONG SONG: Kiểm tra cả 2 loại captcha trong cùng 1 lượt
            cf_found = False
            shopify_found = False

            # Kiểm tra Cloudflare captcha trước (ưu tiên cao hơn)
            try:
                cf_found = cloudflare_captcha(driver, verbose=True)  # BẬT verbose để debug
                if cf_found:
                    print("✅🤖 [BACKGROUND] ĐÃ TỰ ĐỘNG XỬ LÝ CLOUDFLARE CAPTCHA!")
                    time.sleep(2)  # Đợi lâu hơn sau khi solve
            except Exception as e:
                error_msg = str(e)
                # Chỉ log error nếu không phải HTTPConnectionPool (đã handle ở trên)
                if 'HTTPConnectionPool' not in error_msg:
                    print(f"⚠️ [Background] Lỗi Cloudflare captcha: {error_msg[:60]}")

            # Kiểm tra Shopify captcha ngay sau đó (không đợi)
            try:
                shopify_found = shopify_captcha(driver, verbose=False, auto_solve=True)
                if shopify_found:
                    print("✅🤖 [BACKGROUND] ĐÃ TỰ ĐỘNG XỬ LÝ SHOPIFY CAPTCHA!")
                    time.sleep(2)
            except Exception as e:
                error_msg = str(e)
                if 'HTTPConnectionPool' not in error_msg:
                    print(f"⚠️ [Background] Lỗi Shopify captcha: {error_msg[:60]}")

        except Exception as e:
            # Log lỗi tổng thể
            print(f"⚠️ [Background] Lỗi chung: {str(e)[:100]}")

        # Chờ trước khi check lại
        time.sleep(check_interval)

    print("\n" + "="*70)
    print("🛑 CAPTCHA MONITOR ĐÃ DỪNG")
    print(f"   📊 Tổng số lần check: {check_count}")
    print("="*70 + "\n")


def start_captcha_monitor(driver: webdriver.Chrome, check_interval: float = 2.0):
    """
    Khởi động background thread để tự động kiểm tra cả Cloudflare và Shopify captcha.

    ⚠️ QUAN TRỌNG: Nên gọi hàm này NGAY SAU KHI setup driver, TRƯỚC KHI thực hiện bất kỳ task nào.
    Monitor sẽ chạy global trong suốt lifecycle của driver, không chỉ riêng trong login.

    Args:
        driver: Selenium WebDriver instance
        check_interval: Thời gian giữa các lần check (giây). Mặc định 2.0s

    Example:
        driver = setup_driver()
        start_captcha_monitor(driver, check_interval=1.5)  # Bắt đầu monitor
        # ... thực hiện các tasks ...
        stop_captcha_monitor()  # Dừng monitor khi kết thúc
    """
    global _captcha_monitor_active, _captcha_monitor_thread

    # Nếu thread đã chạy, không khởi động lại
    if _captcha_monitor_active and _captcha_monitor_thread and _captcha_monitor_thread.is_alive():
        print("ℹ️ Captcha monitor đã đang chạy.")
        return

    _captcha_monitor_active = True
    _captcha_monitor_thread = threading.Thread(
        target=_captcha_monitor_background,
        args=(driver, check_interval),
        daemon=True  # Daemon thread sẽ tự động kết thúc khi program exit
    )
    _captcha_monitor_thread.start()

    # Đợi một chút để đảm bảo thread đã bắt đầu chạy
    time.sleep(0.5)
    print("✅ Captcha monitor thread đã được khởi động!")
def stop_captcha_monitor():
    """
    Dừng background thread kiểm tra captcha.

    ⚠️ QUAN TRỌNG: Chỉ nên gọi hàm này khi:
    - Kết thúc toàn bộ chương trình / tất cả tasks
    - Chuẩn bị đóng driver/browser
    - Cleanup resources

    KHÔNG nên dừng monitor giữa chừng các tasks vì captcha có thể xuất hiện bất cứ lúc nào.
    """
    global _captcha_monitor_active, _captcha_monitor_thread

    if _captcha_monitor_active:
        print("⏳ Đang dừng captcha monitor...")
        _captcha_monitor_active = False

        # Đợi thread kết thúc (timeout 5s)
        if _captcha_monitor_thread:
            _captcha_monitor_thread.join(timeout=5)

        print("✅ Captcha monitor đã dừng.")

def register_shopify_account(driver: webdriver.Chrome, email: str, password: str, domain: str, name: str, info: str) -> bool:
    print(f"\n{'='*50}\nStarting Shopify registration process\n{'='*50}")

    # # 1. Navigate to Shopify admin homepage
    # signup_url = "https://www.shopify.com/"
    # driver.get(signup_url)
    # delay(2)

    # # 2. Find and click "Start for free" button
    # print("🔍 Tìm button 'Start for free'...")
    # try:
    #     # Tìm button với text "Start for free" hoặc link có chứa /signup
    #     start_button = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((
    #             By.XPATH,
    #             "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start for free') or @data-component-name='start-free-trial']"
    #         ))
    #     )

    #     highlight_element(driver, start_button)
    #     print("✅ Tìm thấy button 'Start for free'. Click...")
    #     start_button.click()
    #     delay(3)

    #     # 3. Wait for new page to load
    #     print("⏳ Đợi trang đăng ký load...")
    #     WebDriverWait(driver, 15).until(
    #         lambda d: d.execute_script("return document.readyState") == "complete"
    #     )
    #     delay(2)

    #     # 5. Find and fill email input
    #     print("🔍 Tìm input email và điền thông tin...")
    #     try:
    #         email_input = WebDriverWait(driver, 10).until(
    #             EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]#account_email, input[name="account[email]"]'))
    #         )
    #         highlight_element(driver, email_input)
    #         email_input.click()
    #         delay(0.5)
    #         email_input.clear()
    #         email_input.send_keys(email)
    #         print(f"✅ Đã điền email: {email}")
    #         delay(1)

    #         # 6. Find and click "Continue with email" button
    #         print("🔍 Tìm và click button 'Continue with email'...")
    #         continue_btn = WebDriverWait(driver, 10).until(
    #             EC.element_to_be_clickable((
    #                 By.XPATH,
    #                 "//button[contains(@class, 'login-button') and @type='submit']//span[contains(text(), 'Continue with email')]/.."
    #             ))
    #         )
    #         highlight_element(driver, continue_btn)
    #         continue_btn.click()
    #         print("✅ Đã click 'Continue with email'.")
    #         delay(3)

    #     except Exception as e:
    #         print(f"⚠️ Lỗi khi điền email hoặc click Continue: {e}")
    #         # Thử cách khác
    #         try:
    #             cont_btn = find_button(driver, ["Continue with email", "Continue"])
    #             if cont_btn:
    #                 highlight_element(driver, cont_btn)
    #                 cont_btn.click()
    #                 print("✅ Đã click 'Continue with email' (fallback).")
    #                 delay(3)
    #         except Exception as e2:
    #             print(f"⚠️ Không thể click Continue button: {e2}")

    #     # 7. Wait for password input and fill it
    #     print("🔍 Đợi input password xuất hiện...")
    #     try:
    #         password_input = WebDriverWait(driver, 15).until(
    #             EC.presence_of_element_located((
    #                 By.CSS_SELECTOR,
    #                 'input#account_password, input[name="account[password]"], input[type="password"][autocomplete="new-password"]'
    #             ))
    #         )
    #         highlight_element(driver, password_input)
    #         password_input.click()
    #         delay(0.5)
    #         password_input.clear()
    #         password_input.send_keys(password)
    #         print(f"✅ Đã điền password.")
    #         delay(1)

    #     except Exception as e:
    #         print(f"⚠️ Lỗi khi điền password: {e}")

    #     # 8. Find and click "I am human" checkbox (in shadow root or iframe)
    #     print("🔍 Tìm và xử lý 'I am human' checkbox...")
    #     try:
    #         human_clicked = shopify_captcha(driver, verbose=True, auto_solve=False)
    #         if human_clicked:
    #             print("✅ Đã xử lý 'I am human' checkbox.")
    #             delay(3)
    #         else:
    #             print("⚠️ Không tìm thấy 'I am human' checkbox. Có thể cần xác minh thủ công.")
    #     except Exception as e:
    #         print(f"⚠️ Lỗi khi xử lý 'I am human': {e}")

    #     # 9. Wait for "Create Shopify account" button to be enabled and visible, then click
    #     print("🔍 Đang đợi button 'Create Shopify account' được enable và visible...")
    #     try:
    #         # Wait for the button to be present, enabled (no disabled attribute), and clickable
    #         create_account_btn = WebDriverWait(driver, 60).until(
    #             lambda d: d.find_element(By.XPATH, "//button[@type='submit' and @name='commit' and contains(@class, 'captcha__submit') and contains(., 'Create Shopify account')]")
    #             if not d.find_element(By.XPATH, "//button[@type='submit' and @name='commit' and contains(@class, 'captcha__submit') and contains(., 'Create Shopify account')]").get_attribute('disabled')
    #             else None
    #         )

    #         # Double check it's clickable
    #         create_account_btn = WebDriverWait(driver, 10).until(
    #             EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @name='commit' and contains(@class, 'captcha__submit') and contains(., 'Create Shopify account')]"))
    #         )

    #         highlight_element(driver, create_account_btn)
    #         print("✅ Button 'Create Shopify account' đã sẵn sàng, đang click ngay...")
    #         create_account_btn.click()
    #         print("✅ Đã click button 'Create Shopify account'.")
    #         delay(3)

    #     except Exception as e:
    #         print(f"⚠️ Lỗi khi đợi hoặc click button 'Create Shopify account': {e}")
    #         print("⚠️ Có thể cần xác minh thủ công.")

    #     print("\n" + "*"*80)
    #     print("✅ Đã hoàn thành các bước tự động. Vui lòng kiểm tra và hoàn thành các bước còn lại (nếu có).")
    #     input("Nhấn Enter khi đã hoàn thành đăng ký...")
    #     print("*"*80 + "\n")

    #     return True

    # except Exception as e:
    #     print(f"❌ Lỗi trong quá trình đăng ký: {e}")
    #     print("\n" + "*"*80)
    #     input("Vui lòng hoàn thành đăng ký thủ công và nhấn Enter để tiếp tục...")
    #     print("*"*80 + "\n")
    #     return False

    # 10. Add card info
    setup_url = "https://admin.shopify.com/signup/38ec7dce-a620-4b94-991d-ba99758ddb12/checkout/extend-trial?locale=en&language=en&signup_page=https%3A%2F%2Fwww.shopify.com%2F&signup_types%5B%5D=paid_trial_experience&_y=8e5df360-2a32-49f6-bfb7-0a65e04750cd&_s=e6ff71a6-6b25-4ec0-ba91-6303b393ddf6&_p=9cafeb48-eeae-4916-906d-42b3055f0cec&country=VN&shopPermanentDomain=wuvx3q-0i.myshopify.com"

    first_name, last_name = extract_fullname(name)
    _, _, address, zip = extract_info(info)

    # Navigate to setup URL and fill card info
    print("🔍 Đang chuyển đến trang setup để thêm thông tin thẻ...")
    driver.get(setup_url)
    delay(2)

    # Wait for page to load
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    delay(1)

    # Fill first name
    print("🔍 Đang đợi input first name...")
    first_name_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="firstName"]'))
    )
    highlight_element(driver, first_name_input)
    first_name_input.click()
    delay(0.5)
    first_name_input.clear()
    first_name_input.send_keys(first_name)
    print(f"✅ Đã điền first name: {first_name}")

    # Fill last name
    print("🔍 Đang đợi input last name...")
    last_name_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="lastName"]'))
    )
    highlight_element(driver, last_name_input)
    last_name_input.click()
    delay(0.5)
    last_name_input.clear()
    last_name_input.send_keys(last_name)
    print(f"✅ Đã điền last name: {last_name}")

    # Fill address
    print("🔍 Đang đợi input address...")
    address_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="address1"]'))
    )
    highlight_element(driver, address_input)
    address_input.click()
    delay(0.5)
    address_input.clear()
    address_input.send_keys(address)
    print(f"✅ Đã điền address: {address}")

    # Fill zip
    print("🔍 Đang đợi input zip...")
    zip_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="zip"]'))
    )
    highlight_element(driver, zip_input)
    zip_input.click()
    delay(0.5)
    zip_input.clear()
    zip_input.send_keys(zip)
    print(f"✅ Đã điền zip: {zip}")

    print("✅ Đã hoàn thành điền thông tin thẻ. Vui lòng kiểm tra và hoàn thành các bước còn lại.")



def extract_hcaptcha_iframe_attributes(driver: webdriver.Chrome, verbose: bool = True) -> dict:
    """
    Tìm và extract sitekey và origin từ hCaptcha iframe src.
    Trả về dictionary chứa sitekey và origin hoặc None nếu không tìm thấy.
    """
    try:
        if verbose:
            print("🔍 Đang tìm hCaptcha iframe...")

        # Tìm tất cả iframe có chứa hcaptcha
        hcaptcha_iframes = driver.find_elements(
            By.CSS_SELECTOR,
            'iframe[src*="hcaptcha.com"], iframe[data-hcaptcha-widget-id]'
        )

        if not hcaptcha_iframes:
            if verbose:
                print("⚠️ Không tìm thấy hCaptcha iframe.")
            return None

        if verbose:
            print(f"✅ Tìm thấy {len(hcaptcha_iframes)} hCaptcha iframe(s).")

        # Extract sitekey và origin từ iframe đầu tiên
        for idx, iframe in enumerate(hcaptcha_iframes):
            try:
                # Get src attribute
                src = iframe.get_attribute('src')

                if not src or 'hcaptcha.com' not in src:
                    continue

                if verbose:
                    print(f"\n{'='*60}")
                    print(f"hCaptcha iframe #{idx + 1}")
                    print(f"{'='*60}")

                # Parse URL để lấy parameters
                from urllib.parse import urlparse, parse_qs, unquote

                # Tách phần fragment (sau dấu #)
                if '#' in src:
                    base_url, fragment = src.split('#', 1)
                    # Parse fragment như query string
                    params = {}
                    for param in fragment.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = unquote(value)

                    # Extract sitekey và origin
                    sitekey = params.get('sitekey', 'N/A')
                    origin = params.get('origin', 'N/A')

                    if verbose:
                        print(f"sitekey: {sitekey}")
                        print(f"origin: {origin}")
                        print(f"{'='*60}\n")

                    # Trả về dict với sitekey và origin
                    return {
                        'sitekey': sitekey,
                        'origin': origin
                    }

            except Exception as e:
                print(f"⚠️ Lỗi khi parse iframe #{idx + 1}: {e}")
                continue

        return None

    except Exception as e:
        print(f"❌ Lỗi khi extract hCaptcha iframe attributes: {e}")
        return None

def shopify_captcha(driver: webdriver.Chrome, verbose: bool = True, auto_solve: bool = False) -> bool:
    """
    Tìm và click vào Shopify captcha 'I am human' checkbox.
    Tìm kiếm trong DOM thông thường, iframe, và shadow root.
    Nếu auto_solve=True, sẽ tự động giải captcha bằng Bright Data.
    """
    # DETECT VÀ PRINT hCaptcha iframe attributes (chỉ khi verbose=True)
    if verbose:
        print("\n🔍 Detecting hCaptcha iframe...")
    captcha_info = extract_hcaptcha_iframe_attributes(driver, verbose=verbose)
    if verbose:
        print("")

    # Nếu tìm thấy hCaptcha và auto_solve được bật, giải captcha tự động
    if captcha_info and auto_solve:
        try:
            import json
            from captcha import solve_shopify_hcaptcha, BrightCaptchaSolver

            # Đọc config để lấy Bright Data credentials
            try:
                with open('env.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    bright_config = config.get('bright_data', {})

                    if bright_config.get('enabled'):
                        api_key = bright_config.get('api_key')
                        zone = bright_config.get('zone')
                        origin = captcha_info.get('origin')

                        if api_key and origin:
                            print("🤖 Bright Data Web Unlocker được bật. Đang tự động bypass hCaptcha...")

                            # Gọi captcha.py để lấy HTML đã bypass
                            html_content = solve_shopify_hcaptcha(origin, api_key, zone)

                            if html_content:
                                # Inject HTML vào driver
                                solver = BrightCaptchaSolver(api_key, zone)
                                if solver.inject_html_to_driver(driver, html_content):
                                    print("✅ Đã bypass và inject HTML thành công!")
                                    return True
                                else:
                                    print("⚠️ Lấy được HTML nhưng inject thất bại. Chuyển sang phương thức thủ công...")
                            else:
                                print("⚠️ Tự động bypass captcha thất bại. Chuyển sang phương thức thủ công...")
                        else:
                            print("⚠️ Thiếu Bright Data API key hoặc origin URL. Chuyển sang phương thức thủ công...")
                    else:
                        if verbose:
                            print("ℹ️ Bright Data không được bật. Sử dụng phương thức thủ công...")
            except FileNotFoundError:
                if verbose:
                    print("⚠️ Không tìm thấy env.json. Chuyển sang phương thức thủ công...")
            except Exception as e:
                if verbose:
                    print(f"⚠️ Lỗi khi đọc config: {e}. Chuyển sang phương thức thủ công...")
        except ImportError:
            if verbose:
                print("⚠️ Không tìm thấy module captcha.py. Chuyển sang phương thức thủ công...")
        except Exception as e:
            if verbose:
                print(f"⚠️ Lỗi khi giải captcha tự động: {e}. Chuyển sang phương thức thủ công...")

    # 2. Tìm trong các iframe
    try:
        if verbose:
            print("   🔍 Đang tìm trong iframe...")

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if verbose:
            print(f"   Tìm thấy {len(iframes)} iframe(s).")

        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                if verbose:
                    print(f"   Đang kiểm tra iframe {i+1}/{len(iframes)}...")

                # Tìm element trong iframe
                human_elements = driver.find_elements(
                    By.XPATH,
                    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i am human')]"
                )

                if human_elements:
                    for elem in human_elements:
                        try:
                            if elem.is_displayed():
                                if verbose:
                                    print(f"   ✅ Tìm thấy 'I am human' trong iframe {i+1}.")
                                elem.click()
                                driver.switch_to.default_content()
                                return True
                        except:
                            continue

                # Thử tìm checkbox hoặc button thông thường
                checkbox_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    'input[type="checkbox"], div[role="checkbox"], button[role="checkbox"]'
                )

                for elem in checkbox_elements:
                    try:
                        if elem.is_displayed():
                            parent_text = driver.execute_script("return arguments[0].parentElement.textContent;", elem).lower()
                            if 'human' in parent_text or 'verify' in parent_text:
                                if verbose:
                                    print(f"   ✅ Tìm thấy checkbox xác minh trong iframe {i+1}.")
                                elem.click()
                                driver.switch_to.default_content()
                                return True
                    except:
                        continue

                driver.switch_to.default_content()

            except Exception as e:
                if verbose:
                    print(f"   ⚠️ Lỗi khi kiểm tra iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Lỗi khi tìm trong iframe: {e}")

    # 3. Tìm trong shadow root
    try:
        if verbose:
            print("   🔍 Đang tìm trong shadow root...")

        # Tìm tất cả elements có shadow root
        elements_with_shadow = driver.execute_script("""
            function findInShadowRoots(root = document.body) {
                let results = [];
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
                let node;
                while (node = walker.nextNode()) {
                    if (node.shadowRoot) {
                        results.push(node);
                    }
                }
                return results;
            }
            return findInShadowRoots();
        """)

        if verbose:
            print(f"   Tìm thấy {len(elements_with_shadow)} element(s) có shadow root.")

        for elem in elements_with_shadow:
            try:
                # Tìm trong shadow root
                shadow_elements = driver.execute_script("""
                    const shadowRoot = arguments[0].shadowRoot;
                    if (!shadowRoot) return [];
                    const allElements = shadowRoot.querySelectorAll('*');
                    return Array.from(allElements).filter(el =>
                        el.textContent.toLowerCase().includes('i am human') ||
                        el.textContent.toLowerCase().includes('verify') ||
                        el.getAttribute('aria-label')?.toLowerCase().includes('human')
                    );
                """, elem)

                if shadow_elements:
                    for shadow_elem in shadow_elements:
                        try:
                            if driver.execute_script("return arguments[0].offsetParent !== null;", shadow_elem):
                                if verbose:
                                    print("   ✅ Tìm thấy 'I am human' trong shadow root.")
                                driver.execute_script("arguments[0].click();", shadow_elem)
                                return True
                        except:
                            continue
            except Exception as e:
                continue
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Lỗi khi tìm trong shadow root: {e}")

    if verbose:
        print("   ⚠️ Không tìm thấy Shopify captcha 'I am human' ở bất kỳ đâu.")
    return False