import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, wait_for_admin, find_button, highlight_element
from sheet import extract_fullname, extract_info

_captcha_monitor_active = False
_captcha_monitor_thread = None

def login_to_shopify(driver: webdriver.Chrome, email: str, password: str, storeId: str) -> bool:
    """Đăng nhập vào Shopify Admin"""
    print(f"\n{'='*50}\nProcessing store ID: {storeId}\n{'='*50}")

    # Captcha monitor sẽ được khởi động ở main() để bảo vệ TẤT CẢ các chức năng
    # Không cần khởi động lại ở đây

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

    # --- Handle Login Screens ---
    email_selectors = 'input[type="email"], input#account_email'
    try:
        email_el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, email_selectors)))
        email_el.clear()
        email_el.send_keys(email)
        print(f"✅ Đã điền email: {email}")
        delay(1)

        # ===== XỬ LÝ SHOPIFY CAPTCHA SAU KHI ĐIỀN EMAIL =====
        print("🔍 Tìm và xử lý Shopify captcha 'I am human'...")
        captcha_handled = shopify_captcha(driver, auto_solve=True)
        if captcha_handled:
            print("✅ Đã xử lý Shopify captcha.")
            delay(2)  # Đợi captcha verify
        else:
            print("⚠️ Không tìm thấy Shopify captcha. Có thể không cần hoặc đã được xử lý.")
            delay(1)

        # Chờ button "Continue with email" visible và clickable
        print("🔍 Đang đợi button 'Continue with email' được enable...")
        keywords_lower = ["continue with email", "tiếp tục bằng email"]
        keyword_conditions = [
            f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k}')"
            for k in keywords_lower
        ]
        xpath_query = (
            f"//button[{' or '.join(keyword_conditions)}] | "
            f"//a[{' or '.join(keyword_conditions)}]"
        )

        cont_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_query))
        )
        highlight_element(driver, cont_btn)
        print("✅ Button 'Continue with email' đã sẵn sàng, đang click...")
        cont_btn.click()
        delay(2)
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
    """Kiểm tra và click vào Cloudflare captcha 'Verify you are human' nếu có"""
    try:
        verify_elements = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify you are human')]"
        )

        if verify_elements:
            if verbose:
                print("✅ Tìm thấy yêu cầu 'Verify you are human'. Click vào...")
            # Tìm element có thể click (button, link, hoặc div có role="button")
            clickable_verify = None

            for elem in verify_elements:
                tag_name = elem.tag_name.lower()
                if tag_name in ['button', 'a'] or elem.get_attribute('role') == 'button':
                    clickable_verify = elem
                    break

            if clickable_verify:
                highlight_element(driver, clickable_verify)
                clickable_verify.click()
                if verbose:
                    print("✅ Đã click vào 'Verify you are human'.")
                delay(3)
                return True
            else:
                # Nếu không tìm thấy element có thể click, thử click vào element đầu tiên
                highlight_element(driver, verify_elements[0])
                verify_elements[0].click()
                if verbose:
                    print("✅ Đã click vào element chứa 'Verify you are human'.")
                delay(3)
                return True
        else:
            return False

    except Exception as e:
        if verbose:
            print(f"⚠️ Lỗi khi kiểm tra/xác minh human: {e}")
        return False


def _cloudflare_captcha_monitor(driver: webdriver.Chrome, check_interval: float = 2.0):
    """Background thread để liên tục kiểm tra và xử lý Cloudflare captcha"""
    global _captcha_monitor_active

    print("🔄 Cloudflare captcha monitor đã bắt đầu (chạy trong background)...")

    while _captcha_monitor_active:
        try:
            # Kiểm tra captcha (không verbose để tránh spam log)
            found = cloudflare_captcha(driver, verbose=False)
            if found:
                print("🤖 [Background] Đã tự động xử lý Cloudflare captcha!")
        except Exception as e:
            # Bỏ qua lỗi để thread tiếp tục chạy
            pass

        # Chờ trước khi check lại
        time.sleep(check_interval)

    print("🛑 Cloudflare captcha monitor đã dừng.")


def start_captcha_monitor(driver: webdriver.Chrome, check_interval: float = 2.0):
    """Khởi động background thread để tự động kiểm tra captcha"""
    global _captcha_monitor_active, _captcha_monitor_thread

    # Nếu thread đã chạy, không khởi động lại
    if _captcha_monitor_active and _captcha_monitor_thread and _captcha_monitor_thread.is_alive():
        print("ℹ️ Captcha monitor đã đang chạy.")
        return

    _captcha_monitor_active = True
    _captcha_monitor_thread = threading.Thread(
        target=_cloudflare_captcha_monitor,
        args=(driver, check_interval),
        daemon=True  # Daemon thread sẽ tự động kết thúc khi program exit
    )
    _captcha_monitor_thread.start()


def stop_captcha_monitor():
    """Dừng background thread kiểm tra captcha"""
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



def extract_hcaptcha_iframe_attributes(driver: webdriver.Chrome) -> dict:
    """
    Tìm và extract sitekey và origin từ hCaptcha iframe src.
    Trả về dictionary chứa sitekey và origin hoặc None nếu không tìm thấy.
    """
    try:
        print("🔍 Đang tìm hCaptcha iframe...")

        # Tìm tất cả iframe có chứa hcaptcha
        hcaptcha_iframes = driver.find_elements(
            By.CSS_SELECTOR,
            'iframe[src*="hcaptcha.com"], iframe[data-hcaptcha-widget-id]'
        )

        if not hcaptcha_iframes:
            print("⚠️ Không tìm thấy hCaptcha iframe.")
            return None

        print(f"✅ Tìm thấy {len(hcaptcha_iframes)} hCaptcha iframe(s).")

        # Extract sitekey và origin từ iframe đầu tiên
        for idx, iframe in enumerate(hcaptcha_iframes):
            try:
                # Get src attribute
                src = iframe.get_attribute('src')

                if not src or 'hcaptcha.com' not in src:
                    continue

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
    # DETECT VÀ PRINT hCaptcha iframe attributes
    print("\n🔍 Detecting hCaptcha iframe...")
    captcha_info = extract_hcaptcha_iframe_attributes(driver)
    print("")

    # Nếu tìm thấy hCaptcha và auto_solve được bật, giải captcha tự động
    if captcha_info and auto_solve:
        try:
            import json
            from captcha import solve_shopify_hcaptcha, BrightCaptchaSolver

            # Đọc config để lấy Bright Data credentials
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
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
                    print("⚠️ Không tìm thấy config.json. Chuyển sang phương thức thủ công...")
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