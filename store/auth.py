from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, wait_for_admin, find_button, highlight_element

def login_to_shopify(driver: webdriver.Chrome, email: str, password: str, storeId: str) -> bool:
    """Đăng nhập vào Shopify Admin"""
    print(f"\n{'='*50}\nProcessing store ID: {storeId}\n{'='*50}")

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

        # Chờ button "Continue with email" visible và clickable
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

def check_and_click_verify_human(driver: webdriver.Chrome) -> bool:
    """Kiểm tra và click vào yêu cầu 'Verify you are human' nếu có"""
    print("🔍 Kiểm tra xem có yêu cầu xác minh 'Verify you are human' không...")
    try:
        verify_elements = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify you are human')]"
        )

        if verify_elements:
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
                print("✅ Đã click vào 'Verify you are human'.")
                delay(3)
                return True
            else:
                # Nếu không tìm thấy element có thể click, thử click vào element đầu tiên
                highlight_element(driver, verify_elements[0])
                verify_elements[0].click()
                print("✅ Đã click vào element chứa 'Verify you are human'.")
                delay(3)
                return True
        else:
            print("ℹ️ Không tìm thấy yêu cầu 'Verify you are human'. Tiếp tục...")
            return False

    except Exception as e:
        print(f"⚠️ Lỗi khi kiểm tra/xác minh human: {e}")
        print("ℹ️ Tiếp tục quá trình đăng ký...")
        return False

def register_shopify_account(driver: webdriver.Chrome, email: str, password: str, storeId: str) -> bool:
    print(f"\n{'='*50}\nStarting Shopify registration process\n{'='*50}")

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

        # 4. Check if "Verify you are human" appears
        check_and_click_verify_human(driver)

        # 5. Find and fill email input
        print("🔍 Tìm input email và điền thông tin...")
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]#account_email, input[name="account[email]"]'))
            )
            highlight_element(driver, email_input)
            email_input.click()  # Focus vào input
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
            password_input.click()  # Focus vào input
            delay(0.5)
            password_input.clear()
            password_input.send_keys(password)
            print(f"✅ Đã điền password.")
            delay(1)

        except Exception as e:
            print(f"⚠️ Lỗi khi điền password: {e}")

        # 8. Find and click "I am human" checkbox (in shadow root or iframe)
        print("🔍 Tìm và click 'I am human' checkbox...")
        try:
            human_clicked = find_and_click_human_verification(driver)
            if human_clicked:
                print("✅ Đã click 'I am human' checkbox.")
                delay(3)
            else:
                print("⚠️ Không tìm thấy 'I am human' checkbox. Có thể cần xác minh thủ công.")
        except Exception as e:
            print(f"⚠️ Lỗi khi tìm 'I am human': {e}")

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

def find_and_click_human_verification(driver: webdriver.Chrome) -> bool:
    # 1. Thử tìm trong DOM thông thường
    try:
        human_elements = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i am human')]"
        )
        if human_elements:
            for elem in human_elements:
                try:
                    if elem.is_displayed():
                        highlight_element(driver, elem)
                        elem.click()
                        return True
                except:
                    continue
    except Exception as e:
        print(f"   Không tìm thấy trong DOM thông thường: {e}")

    # 2. Tìm trong các iframe
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   Tìm thấy {len(iframes)} iframe(s).")

        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
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
                                print(f"   ✅ Tìm thấy checkbox xác minh trong iframe {i+1}.")
                                elem.click()
                                driver.switch_to.default_content()
                                return True
                    except:
                        continue

                driver.switch_to.default_content()

            except Exception as e:
                print(f"   Lỗi khi kiểm tra iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue
    except Exception as e:
        print(f"   Lỗi khi tìm trong iframe: {e}")

    # 3. Tìm trong shadow root
    try:
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

        print(f"Tìm thấy {len(elements_with_shadow)} element(s) có shadow root.")

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
                                print("✅ Tìm thấy 'I am human' trong shadow root.")
                                driver.execute_script("arguments[0].click();", shadow_elem)
                                return True
                        except:
                            continue
            except Exception as e:
                continue
    except Exception as e:
        print(f"Lỗi khi tìm trong shadow root: {e}")

    return False