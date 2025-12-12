"""
utils/element.py - GENERIC HELPER FUNCTIONS
============================================

File này chứa các GENERIC functions có thể REUSE cho mọi module.

NGUYÊN TẮC PHÂN TÁCH:
---------------------
1. GENERIC functions (trong file này):
   - Không chứa logic cụ thể của business
   - Có thể dùng lại ở nhiều nơi khác nhau
   - Ví dụ: find_iframe_with_selector(), wait_for_element_safely(), find_button()

2. SPECIFIC functions (trong từng module riêng như policies.py, pages.py):
   - Chứa logic riêng cho từng feature cụ thể
   - Sử dụng các generic functions từ element.py
   - Ví dụ: inject_tinymce_content() trong policies.py

VÍ DỤ SỬ DỤNG:
--------------
# File policies.py (SPECIFIC):
from utils.element import find_iframe_with_selector  # Import generic function

def inject_tinymce_content(driver, content):  # Specific function
    tinymce = find_iframe_with_selector(driver, "body#tinymce")  # Dùng generic
    if tinymce:
        driver.execute_script("...", tinymce)  # Logic specific
        driver.switch_to.default_content()

# File themes.py (SPECIFIC - có thể dùng lại generic function):
from utils.element import find_iframe_with_selector  # Cùng generic function

def inject_theme_code(driver, code):  # Specific function khác
    editor = find_iframe_with_selector(driver, "div.code-editor")  # Dùng generic
    if editor:
        editor.send_keys(code)  # Logic specific khác
        driver.switch_to.default_content()
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List

from utils.toast import show_toast

def delay(seconds: float):
    time.sleep(seconds)

def highlight_element(driver: webdriver.Chrome, element):
    driver.execute_script(
        "arguments[0].style.outline = '4px solid red'; arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });",
        element
    )

def wait_for_admin(driver: webdriver.Chrome, timeout: int = 120) -> bool:
    print("Waiting for Admin UI to load...")
    try:
        # Kiểm tra nhiều điều kiện để đảm bảo trang admin đã load
        WebDriverWait(driver, timeout).until(
            lambda d: "admin.shopify.com/store/" in d.current_url and d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Admin UI detected (Page loaded successfully).")
        return True
    except Exception as e:
        print(f"⚠️ Admin UI not found within timeout. Error: {e}")
        return False

def find_button(root: webdriver.Chrome, keywords: List[str]):
    keywords_lower = [k.lower() for k in keywords]
    keyword_conditions = [
        f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k}')"
        for k in keywords_lower
    ]
    xpath_query = (
        f"//button[{' or '.join(keyword_conditions)}][1] | "
        f"//a[{' or '.join(keyword_conditions)}][1]"
    )
    try:
        wait = WebDriverWait(root, 5)
        button = wait.until(EC.presence_of_element_located((By.XPATH, xpath_query)))
        return button
    except Exception:
        return None

def click_save_button(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    Tìm và click button Save có type='submit'.
    Kiểm tra cả is_enabled() và aria-disabled="false"
    Return True nếu click thành công, False nếu không.
    """
    print("🔍 Tìm button 'Save' có type='submit'...")
    try:
        save_btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save') and @type='submit']"))
        )

        # Kiểm tra cả is_enabled() và aria-disabled
        is_enabled = save_btn.is_enabled()
        aria_disabled = save_btn.get_attribute("aria-disabled")

        print(f"   Button status: is_enabled={is_enabled}, aria-disabled='{aria_disabled}'")

        # Button phải enabled VÀ aria-disabled phải là "false" (hoặc None)
        if is_enabled and (aria_disabled is None or aria_disabled == "false"):
            highlight_element(driver, save_btn)
            print("✅ Button 'Save' đã enabled và aria-disabled='false'. Click...")
            driver.execute_script("arguments[0].click();", save_btn)
            delay(3)
            print("✅ Đã click 'Save'.")
            return True
        else:
            print("⚠️ Button 'Save' đang disabled hoặc aria-disabled != 'false'.")
            return False

    except Exception as e:
        print(f"⚠️ Không tìm thấy button 'Save' type='submit': {e}")
        # Thử tìm button Save thông thường
        save_btn_fallback = find_button(driver, ["Save"])
        if save_btn_fallback:
            try:
                # Kiểm tra cả is_enabled() và aria-disabled cho fallback button
                is_enabled = save_btn_fallback.is_enabled()
                aria_disabled = save_btn_fallback.get_attribute("aria-disabled")

                print(f"   Fallback button status: is_enabled={is_enabled}, aria-disabled='{aria_disabled}'")

                if is_enabled and (aria_disabled is None or aria_disabled == "false"):
                    highlight_element(driver, save_btn_fallback)
                    print("✅ Tìm thấy button 'Save' (fallback) đã enabled. Click...")
                    driver.execute_script("arguments[0].click();", save_btn_fallback)
                    delay(3)
                    print("✅ Đã click 'Save' (fallback).")
                    return True
                else:
                    print("⚠️ Button 'Save' (fallback) đang disabled hoặc aria-disabled != 'false'.")
                    return False
            except Exception as e2:
                print(f"⚠️ Lỗi khi click 'Save' (fallback): {e2}")
                return False
        else:
            print("⚠️ Không tìm thấy button 'Save' nào.")
            return False

def find_iframe_with_element(driver: webdriver.Chrome, element_id: str, timeout: int = 10) -> bool:
    """
    Tìm và switch vào iframe chứa element với ID được chỉ định.
    Return True nếu tìm thấy và switch thành công, False nếu không.
    """
    print(f"🔍 Đang tìm iframe chứa element với ID '{element_id}'...")
    try:
        # Lấy tất cả các iframe trong trang
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   Tìm thấy {len(iframes)} iframe(s) trong trang.")

        for i, iframe in enumerate(iframes):
            try:
                # Switch vào iframe
                driver.switch_to.frame(iframe)
                print(f"   Đang kiểm tra iframe {i+1}/{len(iframes)}...")

                # Thử tìm element trong iframe
                try:
                    element = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.ID, element_id))
                    )
                    print(f"✅ Tìm thấy element với ID '{element_id}' trong iframe {i+1}!")
                    return True
                except:
                    # Không tìm thấy element trong iframe này
                    driver.switch_to.default_content()
                    continue

            except Exception as e:
                print(f"   Lỗi khi kiểm tra iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue

        # Không tìm thấy element trong bất kỳ iframe nào
        print(f"⚠️ Không tìm thấy element với ID '{element_id}' trong bất kỳ iframe nào.")
        driver.switch_to.default_content()
        return False

    except Exception as e:
        print(f"⚠️ Lỗi khi tìm iframe: {e}")
        driver.switch_to.default_content()
        return False

def wait_for_element_safely(driver: webdriver.Chrome, by, value, timeout: int = 15, poll_frequency: float = 0.5):
    """
    Helper function để chờ element một cách an toàn hơn trong môi trường GUI multi-thread.
    Sử dụng explicit wait thay vì implicit wait để tránh timing issues.

    Args:
        driver: WebDriver instance
        by: Locator strategy (By.XPATH, By.CSS_SELECTOR, etc.)
        value: Locator value
        timeout: Maximum time to wait (seconds)
        poll_frequency: How often to check (seconds)

    Returns:
        WebElement if found, None otherwise
    """
    try:
        element = WebDriverWait(driver, timeout, poll_frequency=poll_frequency).until(
            EC.presence_of_element_located((by, value))
        )
        # Thêm một delay nhỏ để đảm bảo element thực sự sẵn sàng
        time.sleep(0.3)
        return element
    except Exception as e:
        print(f"⚠️ Element not found after {timeout}s: {value}")
        print(f"   Error: {e}")
        return None

def wait_for_clickable_safely(driver: webdriver.Chrome, by, value, timeout: int = 15, poll_frequency: float = 0.5):
    """
    Helper function để chờ element có thể click được.
    Đặc biệt hữu ích trong GUI app khi cần đảm bảo element sẵn sàng trước khi click.

    Args:
        driver: WebDriver instance
        by: Locator strategy (By.XPATH, By.CSS_SELECTOR, etc.)
        value: Locator value
        timeout: Maximum time to wait (seconds)
        poll_frequency: How often to check (seconds)

    Returns:
        WebElement if clickable, None otherwise
    """
    try:
        element = WebDriverWait(driver, timeout, poll_frequency=poll_frequency).until(
            EC.element_to_be_clickable((by, value))
        )
        # Scroll vào view để đảm bảo element visible
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.3)
        return element
    except Exception as e:
        print(f"⚠️ Element not clickable after {timeout}s: {value}")
        print(f"   Error: {e}")
        return None

def find_iframe_with_selector(driver: webdriver.Chrome, css_selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10, max_retries: int = 3):
    """
    GENERIC: Tìm iframe chứa element với CSS selector/XPath bất kỳ và switch vào iframe đó.
    Function này là REUSABLE cho mọi trường hợp cần tìm element trong iframe.

    IMPROVED: Thêm retry logic và wait tốt hơn cho GUI threading environment

    Args:
        driver: WebDriver instance
        css_selector: CSS selector hoặc XPath của element cần tìm
        by: Locator strategy (By.CSS_SELECTOR, By.XPATH, By.ID, etc.)
        timeout: Thời gian chờ tối đa cho mỗi iframe (seconds)
        max_retries: Số lần retry nếu không tìm thấy iframe

    Returns:
        WebElement nếu tìm thấy (và đã switch vào iframe), None nếu không tìm thấy

    Example:
        # Case 1: Tìm TinyMCE editor trong Shopify policies
        tinymce = find_iframe_with_selector(driver, "body#tinymce[contenteditable='true']")
        if tinymce:
            driver.execute_script("arguments[0].innerHTML = '<p>Content</p>';", tinymce)
            driver.switch_to.default_content()

        # Case 2: Tìm Rich Text Editor khác
        editor = find_iframe_with_selector(driver, "div.editor-content", By.CSS_SELECTOR)
        if editor:
            editor.send_keys("Text to input")
            driver.switch_to.default_content()

        # Case 3: Tìm element bằng ID
        form = find_iframe_with_selector(driver, "payment-form", By.ID)
        if form:
            # Do something with form
            driver.switch_to.default_content()

    Note:
        - Function này TỰ ĐỘNG switch vào iframe khi tìm thấy element
        - Sau khi xử lý xong, BẠN PHẢI tự gọi driver.switch_to.default_content()
        - Nếu không tìm thấy, function đã tự switch_to.default_content()
    """
    print(f"🔍 Đang tìm iframe chứa element: {css_selector}...")

    for retry in range(max_retries):
        try:
            if retry > 0:
                print(f"   🔄 Retry #{retry + 1}/{max_retries}...")
                # Đợi lâu hơn giữa các lần retry
                time.sleep(2)
            else:
                # Đợi iframe load - tăng thời gian chờ cho GUI app
                time.sleep(2)

            # Scroll xuống để trigger lazy-load iframe nếu có
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(0.5)

            # Lấy tất cả các iframe trong trang
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"   Tìm thấy {len(iframes)} iframe(s) trong trang.")

            if len(iframes) == 0 and retry < max_retries - 1:
                print(f"   ⚠️ Chưa có iframe nào, retry...")
                continue

            for idx, iframe in enumerate(iframes):
                try:
                    # Kiểm tra iframe có visible không
                    if not iframe.is_displayed():
                        print(f"   ⏭️  Iframe #{idx + 1} không visible, skip...")
                        continue

                    # Switch vào iframe - thêm retry cho trường hợp iframe bị thay đổi
                    switch_success = False
                    for switch_attempt in range(2):  # Retry switch 2 lần
                        try:
                            driver.switch_to.frame(iframe)
                            switch_success = True
                            break
                        except Exception as switch_e:
                            print(f"   ⚠️ Lỗi switch vào iframe #{idx + 1} (attempt {switch_attempt + 1}): {switch_e}")
                            time.sleep(1)
                            continue

                    if not switch_success:
                        print(f"   ❌ Không thể switch vào iframe #{idx + 1} sau 2 lần thử")
                        continue

                    print(f"   Đang kiểm tra iframe #{idx + 1}...")

                    # Tìm element trong iframe với retry logic
                    element_found = False
                    for element_attempt in range(3):  # Retry tìm element 3 lần
                        try:
                            element = WebDriverWait(driver, timeout).until(
                                EC.presence_of_element_located((by, css_selector))
                            )

                            # Đợi thêm để đảm bảo element ready
                            time.sleep(0.5)

                            # Verify element thực sự có thể tương tác
                            if element.is_displayed():
                                print(f"✅ Tìm thấy element trong iframe #{idx + 1}!")
                                # GIỮ NGUYÊN việc switch vào iframe, function gọi sẽ tự switch_to.default_content()
                                return element
                            else:
                                print(f"   ⚠️ Element tìm thấy nhưng không visible trong iframe #{idx + 1}")
                                element_found = True  # Đánh dấu đã tìm thấy nhưng không visible
                                break

                        except Exception as element_e:
                            if "no such element" in str(element_e).lower():
                                print(f"   ⚠️ Element chưa sẵn sàng trong iframe #{idx + 1} (attempt {element_attempt + 1}): {element_e}")
                                if element_attempt < 2:  # Còn retry
                                    time.sleep(1)
                                    continue
                                else:
                                    print(f"   ❌ Không tìm thấy element sau 3 lần thử trong iframe #{idx + 1}")
                                    break
                            else:
                                # Lỗi khác (không phải no such element)
                                print(f"   ❌ Lỗi khác khi tìm element trong iframe #{idx + 1}: {element_e}")
                                break

                    # Nếu element không visible hoặc không tìm thấy, switch back và tiếp tục
                    if not element_found:
                        driver.switch_to.default_content()
                        continue
                    else:
                        # Element found but not visible, switch back
                        driver.switch_to.default_content()
                        continue

                except Exception as e:
                    print(f"   Lỗi khi kiểm tra iframe #{idx + 1}: {e}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                    continue

            # Nếu đã check hết iframe mà không thấy
            if retry < max_retries - 1:
                print(f"   ⚠️ Không tìm thấy trong lần này, retry...")
                driver.switch_to.default_content()
                continue
            else:
                # Hết retry
                print(f"⚠️ Không tìm thấy element '{css_selector}' trong bất kỳ iframe nào sau {max_retries} lần thử.")
                driver.switch_to.default_content()
                return None

        except Exception as e:
            print(f"⚠️ Lỗi khi tìm iframe (retry {retry + 1}/{max_retries}): {e}")
            try:
                driver.switch_to.default_content()
            except:
                pass

            if retry < max_retries - 1:
                continue
            else:
                return None

    return None

def detect_store_id(driver: webdriver.Chrome) -> str:
    show_toast(driver, "🔍 Đang lấy store id...")
    driver.get("https://admin.shopify.com")

    try:
        # Tăng timeout lên 45s để phù hợp với GUI app
        WebDriverWait(driver, 45).until(
            lambda d: "admin.shopify.com/store/" in d.current_url
        )

        current_url = driver.current_url
        if "/store/" in current_url:
            store_id = current_url.split("/store/")[1].split("/")[0]
            print(f"✅ Detected store_id: {store_id}")
            return store_id
        else:
            print("⚠️ Redirected but store_id not found in URL.")
            return None

    except Exception as e:
        print(f"⚠️ Failed to detect store_id: {e}")
        return None
