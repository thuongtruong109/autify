import json
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any

def get_config_path():
    """Get the correct path to config.json whether running as script or exe"""
    if getattr(sys, 'frozen', False):
        # Running as exe - config.json should be in the same folder as exe
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, "./config.json")
    else:
        # Running as script - config.json is in the same folder as utils.py
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "./config.json")

CRED_PATH = get_config_path()

def delay(seconds: float):
    time.sleep(seconds)

def load_credentials_from_json() -> Dict[str, Any]:
    """Load credentials from config.json file"""
    print(f"Attempting to load credentials from: {CRED_PATH}")
    if not os.path.exists(CRED_PATH):
        print(f"Error: {CRED_PATH} not found.")
        return {}

    with open(CRED_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parse error in config.json: {e}")
        return {}

    if not isinstance(data, dict):
        print(f"Error: config.json must be a single object, not an array or other type.")
        return {}

    if not (data.get("email") and data.get("password") and data.get("storeId")):
        print(f"Error: config.json missing required fields: email, password, storeId")
        return {}

    print(f"Loaded credentials for store: {data['storeId']}")
    return data

def load_credentials(use_sheet: bool = True, row_index: int = 0) -> Dict[str, Any]:
    """
    Load credentials from Google Sheet or JSON config file.
    Args:
        use_sheet: If True, load from Google Sheet; if False, load from config.json
        row_index: Row index to load from Google Sheet (default: 0 = first row)
    """
    if use_sheet:
        try:
            from sheet import get_credentials_from_sheet
            print("📊 Loading credentials from Google Sheet...")
            credentials = get_credentials_from_sheet(row_index)
            if credentials:
                return credentials
            print("⚠️ Failed to load from Google Sheet. Falling back to config.json...")
        except ImportError:
            print("⚠️ sheet.py not found. Falling back to config.json...")
        except Exception as e:
            print(f"⚠️ Error loading from Google Sheet: {e}. Falling back to config.json...")

    # Fallback to JSON config
    return load_credentials_from_json()

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