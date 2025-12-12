from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, wait_for_admin, find_button, highlight_element
from utils.toast import show_toast

def login_to_shopify(driver: webdriver.Chrome, email: str, password: str, storeId: str) -> bool:
    login_url = f"https://admin.shopify.com/store/{storeId}"
    driver.get(login_url)
    delay(1)

    print("Checking login status...")
    # Tăng timeout lên 15s để ổn định hơn trong GUI app
    logged = wait_for_admin(driver, 15)

    if logged:
        print("✅ Already logged in. Skipping login steps.")
        return True

    print("⚠️ Not logged in. Starting login process...")

    email_selectors = 'input[type="email"], input#account_email'
    try:
        show_toast(driver, "🔍 Finding email input")
        # Tăng timeout lên 20s cho GUI app
        email_el = WebDriverWait(driver, 20, poll_frequency=0.5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, email_selectors))
        )
        # Thêm delay nhỏ để đảm bảo element sẵn sàng
        delay(0.3)
        email_el.clear()
        delay(0.2)
        email_el.send_keys(email)
        show_toast(driver, f"✅ Filled email")
        delay(0.5)

        show_toast(driver, "🔍 Finding 'Continue with email' button")
        keywords_lower = ["continue with email", "tiếp tục bằng email"]
        keyword_conditions = [
            f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k}')"
            for k in keywords_lower
        ]
        xpath_query = (
            f"//button[{' or '.join(keyword_conditions)}] | "
            f"//a[{' or '.join(keyword_conditions)}]"
        )

        show_toast(driver, "⏳ Waiting for 'Continue with email' button")
        # Tăng timeout lên 20s và thêm poll_frequency
        cont_btn = WebDriverWait(driver, 20, poll_frequency=0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath_query))
        )
        highlight_element(driver, cont_btn)
        show_toast(driver, "✅ 'Continue with email' button is visible")
        delay(0.3)
        cont_btn.click()
        show_toast(driver, "✅ Clicked 'Continue with email' button")
        delay(2)

    except Exception as e:
        print(f"⚠️ Lỗi khi xử lý email input hoặc click continue button: {e}")
        print("💡 Có thể cần xử lý captcha hoặc login thủ công")
        pass

    pass_selectors = 'input[type="password"], input#account_password'
    try:
        # Tăng timeout lên 10s cho password field
        pass_el = WebDriverWait(driver, 10, poll_frequency=0.5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, pass_selectors))
        )
        delay(0.3)
        pass_el.clear()
        delay(0.2)
        pass_el.send_keys(password)
        delay(0.5)

        login_btn = find_button(driver, ["Log in", "Đăng nhập"])
        if login_btn:
            delay(0.3)
            login_btn.click()
    except Exception:
        pass

    print("Solve CAPTCHA/2FA manually if needed...")
    # Tăng timeout lên 90s cho bước này (có thể có captcha)
    logged = wait_for_admin(driver, 90)

    if not logged:
        print("\n" + "*"*80)
        input("Admin UI not detected. Please login manually in the browser. Press Enter here when complete...")
        print("*"*80 + "\n")

        logged = wait_for_admin(driver, 15)

    return logged

def register_shopify_account(driver: webdriver.Chrome, email: str, password: str, domain: str, first_name: str, last_name: str, address: str, zip: str, card_number: str, card_expired: str, card_cvc: str) -> bool:
    # # 1. Navigate to Shopify admin homepage
    # signup_url = "https://admin.shopify.com/signup"
    # driver.get(signup_url)
    # delay(2)

    # # 2. Find and click "Start for free" button
    # print("🔍 Tìm button 'Start for free'...")
    # try:

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

    #         # Đợi page transition sau khi click Continue
    #         print("⏳ Đợi page transition để password input xuất hiện...")
    #         delay(1)

    #         # Đợi page load xong
    #         WebDriverWait(driver, 15).until(
    #             lambda d: d.execute_script("return document.readyState") == "complete"
    #         )
    #         print("✅ Page đã load xong.")
    #         delay(1)

    #     except Exception as e:
    #         print(f"⚠️ Lỗi khi điền email hoặc click Continue: {e}")
    #         try:
    #             cont_btn = find_button(driver, ["Continue with email", "Continue"])
    #             if cont_btn:
    #                 highlight_element(driver, cont_btn)
    #                 cont_btn.click()
    #                 print("✅ Đã click 'Continue with email' (fallback).")

    #                 # Đợi page transition
    #                 print("⏳ Đợi page transition...")
    #                 delay(3)
    #                 WebDriverWait(driver, 15).until(
    #                     lambda d: d.execute_script("return document.readyState") == "complete"
    #                 )
    #                 delay(1)
    #         except Exception as e2:
    #             print(f"⚠️ Không thể click Continue button: {e2}")

    #     # 7. Wait for password input and fill it
    #     print("\n🔍 Bắt đầu tìm và điền password input...")
    #     print(f"🔍 Current URL: {driver.current_url}")

    #     try:
    #         # Debug: Check what's on page
    #         print("🔍 Checking page for password inputs...")
    #         try:
    #             all_password_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
    #             print(f"📋 Found {len(all_password_inputs)} password input(s) on page")
    #             for idx, inp in enumerate(all_password_inputs):
    #                 inp_id = inp.get_attribute('id')
    #                 inp_name = inp.get_attribute('name')
    #                 inp_visible = inp.is_displayed()
    #                 print(f"   [{idx}] ID: '{inp_id}', Name: '{inp_name}', Visible: {inp_visible}")
    #         except:
    #             pass

    #         # Tìm password input với ID cụ thể
    #         print("🔍 Đang tìm password input với ID='account_password'...")

    #         # Đợi element present trước
    #         password_input = WebDriverWait(driver, 20).until(
    #             EC.presence_of_element_located((By.ID, 'account_password'))
    #         )
    #         print("✅ Tìm thấy password input (present)")

    #         # Đợi element visible
    #         print("⏳ Đợi password input visible...")
    #         password_input = WebDriverWait(driver, 10).until(
    #             EC.visibility_of_element_located((By.ID, 'account_password'))
    #         )
    #         print("✅ Password input đã visible!")

    #         # Kiểm tra có bị che không
    #         is_displayed = password_input.is_displayed()
    #         is_enabled = password_input.is_enabled()
    #         print(f"📋 Password input state: displayed={is_displayed}, enabled={is_enabled}")

    #         # Scroll vào view để đảm bảo visible
    #         print("📜 Scroll password input vào view...")
    #         driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", password_input)
    #         delay(0.8)

    #         # Highlight để debug
    #         highlight_element(driver, password_input)

    #         # Click để focus
    #         print("�️ Click vào password input để focus...")
    #         try:
    #             password_input.click()
    #         except:
    #             # Fallback: click bằng JavaScript
    #             print("⚠️ Click thường failed, dùng JavaScript...")
    #             driver.execute_script("arguments[0].click();", password_input)
    #         delay(0.5)

    #         # Clear existing value
    #         print("🧹 Clear password input...")
    #         password_input.clear()
    #         delay(0.3)

    #         # Điền password
    #         print(f"⌨️ Điền password (length: {len(password)})...")
    #         password_input.send_keys(password)
    #         delay(0.5)

    #         # Verify đã điền
    #         current_value = password_input.get_attribute('value')
    #         if current_value:
    #             print(f"✅ Đã điền password thành công! (length: {len(current_value)})")
    #         else:
    #             print(f"⚠️ Password input vẫn trống, thử lại với JavaScript...")
    #             driver.execute_script(f"arguments[0].value = '{password}';", password_input)
    #             # Trigger input event
    #             driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password_input)
    #             driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password_input)
    #             print(f"✅ Đã điền password bằng JavaScript!")

    #         delay(1)

    #     except Exception as e:
    #         print(f"❌ Lỗi khi điền password: {e}")
    #         import traceback
    #         print(f"📋 Traceback: {traceback.format_exc()}")
    #         print("⚠️ Có thể cần điền password thủ công!")

    #     # 8. Background monitor sẽ tự động xử lý captcha nếu có
    #     print("ℹ️  Background captcha monitor đang chạy - sẽ tự động xử lý 'I am human' nếu xuất hiện")
    #     print("⏳ Đợi một chút để monitor có thời gian xử lý...")
    #     delay(3)

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
    setup_url = "https://admin.shopify.com/signup/43c18866-413c-4d75-9248-2089c3d593c8/checkout/extend-trial?country=VN&shopPermanentDomain=5h5huv-zz.myshopify.com"

    print("\n" + "="*70)
    print("🔍 NAVIGATING TO SETUP PAGE")
    print("="*70)
    print(f"Target URL: {setup_url}")
    driver.get(setup_url)
    delay(2)

    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    delay(1)

    actual_url = driver.current_url
    print(f"Actual URL: {actual_url}")

    if actual_url != setup_url:
        print("⚠️  WARNING: URL CHANGED! Page may have redirected!")
        print(f"   Expected: {setup_url}")
        print(f"   Got: {actual_url}")
    else:
        print("✅ URL matches - on correct page")
    print("="*70 + "\n")

    show_toast(driver, "Filling form fields...")

    # BREAKTHROUGH: Wait for fields to be ready, then fill with JavaScript!
    print("Waiting for form fields to be ready...")

    # STEP 1: OPTIMIZED - Wait until ALL required inputs exist and are visible
    print("⏳ Waiting for form fields (optimized check)...")
    max_attempts = 15  # Reduced from 30 to 15 (3s max instead of 6s)
    check_interval = 0.2  # Check mỗi 0.2s

    for attempt in range(max_attempts):
        check_result = driver.execute_script("""
            // Kiểm tra page load state trước
            if (document.readyState !== 'complete') {
                return { ready: false, status: { reason: 'page still loading' } };
            }

            const requiredFields = ['firstName', 'lastName', 'address1', 'zip'];
            const status = {};
            let allReady = true;

            for (const name of requiredFields) {
                const input = document.querySelector(`input[name="${name}"]`);
                if (!input) {
                    status[name] = 'not found';
                    allReady = false;
                } else if (input.offsetParent === null) {
                    status[name] = 'not visible';
                    allReady = false;
                } else {
                    status[name] = 'ready';
                }
            }

            return { ready: allReady, status: status };
        """)

        if check_result['ready']:
            elapsed_time = (attempt + 1) * check_interval
            print(f"✅ Form fields ready after {attempt + 1} checks ({elapsed_time:.1f}s)")
            print(f"   Field status: {check_result['status']}")
            break
        else:
            if attempt == 0 or attempt % 10 == 0:  # Log less frequently
                print(f"   Check {attempt + 1}/{max_attempts}: {check_result['status']}")
        delay(check_interval)
    else:
        print("❌ WARNING: Timeout waiting for form fields!")
        print(f"   Final status: {check_result['status']}")    # STEP 2: Validate input values
    print("Validating input values...")
    if not first_name or not first_name.strip():
        print("❌ ERROR: first_name is empty!")
    if not last_name or not last_name.strip():
        print("❌ ERROR: last_name is empty!")
    if not address or not address.strip():
        print("❌ ERROR: address is empty!")
    if not zip or not zip.strip():
        print("❌ ERROR: zip is empty!")

    # STEP 3: DEBUG - Check actual page state
    print("\n" + "="*70)
    print("DEBUG: CHECKING PAGE STATE BEFORE FILLING")
    print("="*70)

    current_url = driver.current_url
    page_title = driver.title
    print(f"Current URL: {current_url}")
    print(f"Page Title: {page_title}")

    # Check what inputs actually exist
    page_inputs = driver.execute_script("""
        const inputs = document.querySelectorAll('input');
        const data = {
            total: inputs.length,
            visible: 0,
            names: []
        };
        inputs.forEach(inp => {
            if (inp.offsetParent !== null) {
                data.visible++;
                data.names.push({
                    name: inp.name || '',
                    id: inp.id || '',
                    type: inp.type
                });
            }
        });
        return data;
    """)

    print(f"Total inputs on page: {page_inputs['total']}")
    print(f"Visible inputs: {page_inputs['visible']}")
    print(f"Input names: {page_inputs['names']}")
    print("="*70 + "\n")

    # STEP 4: Now fill all fields with JavaScript
    print("Filling form fields with JavaScript...")
    print(f"DEBUG VALUES:")
    print(f"  first_name='{first_name}' (len={len(first_name) if first_name else 0})")
    print(f"  last_name='{last_name}' (len={len(last_name) if last_name else 0})")
    print(f"  address='{address}' (len={len(address) if address else 0})")
    print(f"  zip='{zip}' (len={len(zip) if zip else 0})")
    delay(0.5)

    result = driver.execute_script("""
        const fields = {
            firstName: arguments[0],
            lastName: arguments[1],
            address1: arguments[2],
            zip: arguments[3]
        };

        const results = {};
        const debug = {};
        for (const [name, value] of Object.entries(fields)) {
            const input = document.querySelector(`input[name="${name}"]`);
            if (!input) {
                results[name] = false;
                debug[name] = 'input not found';
            } else if (input.offsetParent === null) {
                results[name] = false;
                debug[name] = 'input not visible';
            } else {
                try {
                    // REACT FIX: Use native setter to trigger React's onChange
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype,
                        'value'
                    ).set;
                    nativeInputValueSetter.call(input, value);

                    // Trigger ONLY essential events (không dùng blur để tránh reset form!)
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));

                    // Focus để activate field (không blur!)
                    input.focus();

                    results[name] = true;
                    debug[name] = 'success';
                } catch (e) {
                    results[name] = false;
                    debug[name] = 'error: ' + e.message;
                }
            }
        }
        return { results: results, debug: debug };
    """, first_name, last_name, address, zip)

    # STEP 5: Verify and highlight
    print(f"DEBUG: JavaScript returned: {result}")

    actual_results = result.get('results', result)
    debug_info = result.get('debug', {})

    fields_map = {'firstName': first_name, 'lastName': last_name, 'address1': address, 'zip': zip}
    all_ok = True

    # Extra delay to let React update
    delay(0.5)

    for field_name, value in fields_map.items():
        if actual_results.get(field_name):
            try:
                elem = driver.find_element(By.CSS_SELECTOR, f'input[name="{field_name}"]')

                # Verify value is actually in the input
                actual_value = elem.get_attribute('value')
                if actual_value == value:
                    print(f"✅ {field_name}: {value} (VERIFIED)")
                else:
                    print(f"⚠️  {field_name}: Expected '{value}', got '{actual_value}'")

                highlight_element(driver, elem)
                delay(0.2)
            except Exception as e:
                print(f"⚠️  {field_name}: Error verifying - {e}")
                pass
        else:
            debug_msg = debug_info.get(field_name, 'unknown error')
            print(f"❌ FAILED: {field_name} - {debug_msg}")
            all_ok = False

    if not all_ok:
        print("\n" + "="*60)
        print("FORM FILLING FAILED - DEBUG INFO:")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        print(f"Debug details: {debug_info}")

        # Check what inputs actually exist on page
        all_inputs = driver.execute_script("""
            const inputs = document.querySelectorAll('input');
            const data = [];
            inputs.forEach(inp => {
                if (inp.offsetParent !== null) {
                    data.push({
                        name: inp.name,
                        id: inp.id,
                        type: inp.type,
                        value: inp.value.substring(0, 20)
                    });
                }
            });
            return data;
        """)
        print(f"Visible inputs on page: {all_inputs}")
        print("="*60 + "\n")

        # DON'T RAISE - just warn and continue
        print("⚠️  WARNING: Some fields failed but continuing anyway...")
        print("⚠️  Please fill missing fields manually if needed.\n")

    show_toast(driver, "Filling card information...")

    # Card fields are on MAIN PAGE (not in iframes) - fill them like other fields!
    print("\n🔍 Filling card fields (on main page)...")

    # Add card fields to the same batch fill
    card_result = driver.execute_script("""
        const cardFields = {
            number: arguments[0],
            expiry: arguments[1],
            verification_value: arguments[2]
        };

        const results = {};
        const debug = {};

        for (const [fieldName, value] of Object.entries(cardFields)) {
            // Try multiple selectors for each card field
            let input = document.querySelector(`input[id="${fieldName}"]`);
            if (!input) input = document.querySelector(`input[name="${fieldName}"]`);
            if (!input && fieldName === 'number') {
                input = document.querySelector('input[autocomplete="cc-number"]');
            }
            if (!input && fieldName === 'expiry') {
                input = document.querySelector('input[autocomplete="cc-exp"]');
            }
            if (!input && fieldName === 'verification_value') {
                input = document.querySelector('input[autocomplete="cc-csc"]');
            }

            if (!input) {
                results[fieldName] = false;
                debug[fieldName] = 'input not found';
            } else if (input.offsetParent === null) {
                results[fieldName] = false;
                debug[fieldName] = 'input not visible';
            } else {
                try {
                    // Use native setter for React
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype,
                        'value'
                    ).set;
                    nativeInputValueSetter.call(input, value);

                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    input.focus();

                    const actualValue = input.value;
                    results[fieldName] = actualValue.length > 0;
                    debug[fieldName] = actualValue.length > 0 ? `filled: ${actualValue}` : 'value not set';
                } catch (e) {
                    results[fieldName] = false;
                    debug[fieldName] = 'error: ' + e.message;
                }
            }
        }
        return { results: results, debug: debug };
    """, card_number, card_expired, card_cvc)

    # Verify card fields
    card_results = card_result.get('results', {})
    card_debug = card_result.get('debug', {})

    card_names = {'number': 'Card Number', 'expiry': 'Expiry Date', 'verification_value': 'CVC'}
    for field_key, field_label in card_names.items():
        if card_results.get(field_key):
            print(f"✅ {field_label}: {card_debug.get(field_key, 'OK')}")
        else:
            print(f"❌ {field_label}: {card_debug.get(field_key, 'FAILED')}")

    delay(0.5)

    print("✅ Completed filling card information. Please verify and complete remaining steps.")