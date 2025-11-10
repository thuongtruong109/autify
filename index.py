import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any, Optional
import inquirer

# --- Configuration ---

CRED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

APPS = [
    {"name": "Track123", "slug": "track123", "type": "modal"},
    {"name": "Selleasy", "slug": "upsell-cross-sell-kit-1", "type": "new_tab"},
    {"name": "Judge.me Reviews", "slug": "judgeme", "type": "new_tab"},
    {"name": "Judge.me Importer", "slug": "aliexpress-review-importer", "type": "new_tab"},
    {"name": "Section Store", "slug": "section-factory", "type": "modal"},
    {"name": "Flow", "slug": "flow", "type": "simple"},
    {"name": "Nabu for FB Pixel", "slug": "nabu-for-facebook-pixel", "type": "new_tab"},
    {"name": "DSers-AliExpress Dropshipping", "slug": "dsers", "type": "new_tab"},
]

# --- Utility Functions ---

def delay(seconds: float):
    time.sleep(seconds)

def load_credentials() -> Dict[str, Any]:
    print(f"Attempting to load credentials from: {CRED_PATH}")
    if not os.path.exists(CRED_PATH):
        print(f"Error: {CRED_PATH} not found.")
        return {}

    with open(CRED_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parse error in data.json: {e}")
        return {}

    if not isinstance(data, dict):
        print(f"Error: data.json must be a single object, not an array or other type.")
        return {}

    if not (data.get("email") and data.get("password") and data.get("storeId")):
        print(f"Error: data.json missing required fields: email, password, storeId")
        return {}

    print(f"Loaded credentials for store: {data['storeId']}")
    return data

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

def click_all_install_buttons(driver: webdriver.Chrome, max_attempts: int = 5):
    """Tìm và click TẤT CẢ install buttons có thể tìm thấy (trong trang chính VÀ modal)"""
    install_keywords = ["install app", "install", "add app"]
    click_count = 0  # Đếm số lần click
    clicked_in_modal = False  # Đánh dấu đã click trong modal

    for attempt in range(max_attempts):
        print(f"\n🔍 [Attempt {attempt + 1}/{max_attempts}] Tìm kiếm install button...")

        found_and_clicked = False

        # 1. Kiểm tra xem app đã được install chưa (có nút "Open")
        open_keywords = ["open app", "open"]
        try:
            open_btn = find_button(driver, open_keywords)
            if open_btn:
                # KIỂM TRA KỸ HỞN - chỉ return True nếu THẬT SỰ có nút Open
                btn_text = open_btn.text.lower()
                if 'open' in btn_text and 'install' not in btn_text:
                    print(f"✅ App đã được install (tìm thấy nút 'Open'). Bỏ qua.")
                    return True  # Return True = đã install rồi
        except:
            pass

        # 2. Tìm modal TRƯỚC (ưu tiên modal)
        modal_xpath = "//div[contains(@class, 'Polaris-Modal-Dialog__Modal') or contains(@class, 'modal') or contains(@role, 'dialog')]"
        try:
            modals = driver.find_elements(By.XPATH, modal_xpath)
            if modals:
                for modal in modals:
                    try:
                        # Kiểm tra modal có visible không
                        if not modal.is_displayed():
                            continue

                        print(f"✅ Tìm thấy modal visible. Tìm install button trong modal...")

                        # Thử nhiều cách tìm button trong modal
                        modal_btn = None

                        # Cách 1: Tìm bằng text "install" hoặc "add"
                        try:
                            modal_btn = modal.find_element(By.XPATH, ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'install') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add')]")
                        except:
                            pass

                        # Cách 2: Tìm primary button
                        if not modal_btn:
                            try:
                                modal_btn = modal.find_element(By.XPATH, ".//button[contains(@class, 'Polaris-Button--primary') or contains(@class, 'primary') or contains(@class, 'btn-primary')]")
                            except:
                                pass

                        # Cách 3: Tìm button đầu tiên trong modal (không phải cancel/close)
                        if not modal_btn:
                            try:
                                all_btns = modal.find_elements(By.XPATH, ".//button")
                                for btn in all_btns:
                                    btn_text = btn.text.lower()
                                    if 'cancel' not in btn_text and 'close' not in btn_text and btn.is_displayed():
                                        modal_btn = btn
                                        break
                            except:
                                pass

                        if modal_btn and modal_btn.is_displayed():
                            highlight_element(driver, modal_btn)
                            print(f"✅ Tìm thấy install button trong modal. Text: '{modal_btn.text}'. Click...")
                            driver.execute_script("arguments[0].click();", modal_btn)
                            delay(5)
                            click_count += 1
                            clicked_in_modal = True
                            print(f"✅ Đã click install button trong modal (click #{click_count}).")
                            found_and_clicked = True

                            # SAU KHI CLICK MODAL, DỪNG LẠI (chỉ click 2 lần: trang chính + modal)
                            if click_count >= 2:
                                print(f"✅ Đã click đủ 2 lần (trang chính + modal). Dừng lại.")
                                return False
                            break
                    except Exception as e:
                        print(f"⚠️ Lỗi khi xử lý modal: {e}")
                        continue
        except Exception as e:
            print(f"⚠️ Không tìm thấy modal: {e}")

        # 3. Nếu không có modal, tìm install button trong trang chính
        if not found_and_clicked:
            install_btn = find_button(driver, install_keywords)

            # NẾU KHÔNG TÌM THẤY, THỬ TÌM TẤT CẢ BUTTONS VÀ IN RA
            if not install_btn:
                print(f"⚠️ Không tìm thấy install button bằng keywords. Tìm tất cả buttons...")
                try:
                    all_buttons = driver.find_elements(By.XPATH, "//button | //a[contains(@class, 'button') or contains(@class, 'btn')]")
                    print(f"📝 Tìm thấy {len(all_buttons)} buttons. In ra 10 button đầu tiên:")
                    for i, btn in enumerate(all_buttons[:10]):
                        try:
                            if btn.is_displayed():
                                btn_text = btn.text.strip()
                                btn_classes = btn.get_attribute('class')
                                print(f"   Button {i+1}: Text='{btn_text}' | Classes='{btn_classes}'")

                                # Tìm button có text chứa "install" hoặc "add"
                                if btn_text and ('install' in btn_text.lower() or 'add' in btn_text.lower()):
                                    install_btn = btn
                                    print(f"   ✅ Tìm thấy button phù hợp!")
                                    break
                        except:
                            pass
                except Exception as e:
                    print(f"⚠️ Lỗi khi tìm buttons: {e}")

            if install_btn:
                try:
                    highlight_element(driver, install_btn)
                    print(f"✅ Tìm thấy install button trong trang chính. Text: '{install_btn.text}'. Click...")
                    driver.execute_script("arguments[0].click();", install_btn)
                    delay(5)
                    click_count += 1
                    print(f"✅ Đã click install button trong trang chính (click #{click_count}).")
                    found_and_clicked = True
                except Exception as e:
                    print(f"⚠️ Lỗi khi click: {e}")

        # 4. Nếu đã click trong modal, dừng lại
        if clicked_in_modal:
            print(f"✅ Đã click trong modal. Dừng retry.")
            break

        # 5. Nếu không tìm thấy gì, thoát
        if not found_and_clicked:
            print(f"⚠️ Không tìm thấy install button nào nữa ở attempt {attempt + 1}.")

            # IN RA THÔNG TIN DEBUG
            if attempt == 0:  # Chỉ in ở lần đầu tiên
                print(f"\n📝 DEBUG INFO:")
                print(f"   Current URL: {driver.current_url}")
                print(f"   Page Title: {driver.title}")

                # Kiểm tra xem có phải trang admin không
                if 'admin.shopify.com' in driver.current_url:
                    print(f"   ✅ Đang ở trang admin Shopify")
                elif 'apps.shopify.com' in driver.current_url:
                    print(f"   ✅ Đang ở trang Shopify App Store")
                else:
                    print(f"   ⚠️ Không rõ trang nào")

            # Nếu đã thử 2 lần mà không thấy, dừng lại
            if attempt >= 1:
                break

    print(f"✅ Hoàn tất việc tìm và click install buttons (tổng {click_count} lần).")

    if click_count == 0:
        print(f"⚠️ CẢNH BÁO: Không click được button nào! App có thể chưa được cài đặt.")

    return False  # Return False = chưa install (hoặc không chắc)

def check_installed_apps(driver: webdriver.Chrome, storeId: str, force_reload: bool = False) -> List[str]:
    """Kiểm tra danh sách apps đã được install"""
    print("\n" + "="*60)
    print("🔍 KIỂM TRA APPS ĐÃ ĐƯỢC INSTALL...")
    print("="*60)

    installed_apps = []
    apps_url = f"https://admin.shopify.com/store/{storeId}/settings/apps?link_source=search&before=&after=&tab=installed"

    print(f"Đang vào trang danh sách apps: {apps_url}")
    driver.get(apps_url)

    if force_reload:
        print("🔄 Force reload page để cập nhật danh sách apps...")
        driver.refresh()
        delay(3)

    delay(5)

    # Tìm tất cả app names trên trang
    try:
        # Tìm tất cả text có thể là tên app
        app_elements = driver.find_elements(By.XPATH, "//span | //div | //h2 | //h3")

        print(f"\n📋 Kiểm tra từng app trong danh sách APPS:")
        for app in APPS:
            app_name_lower = app['name'].lower()
            found = False

            for element in app_elements:
                try:
                    element_text = element.text.strip().lower()
                    if element_text and app_name_lower in element_text:
                        installed_apps.append(app['name'])
                        print(f"   ✅ {app['name']} - ĐÃ INSTALL")
                        found = True
                        break
                except:
                    continue

            if not found:
                print(f"   ❌ {app['name']} - CHƯA INSTALL")

        print(f"\n📊 Tổng kết: {len(installed_apps)}/{len(APPS)} apps đã được install")

    except Exception as e:
        print(f"⚠️ Lỗi khi kiểm tra apps đã install: {e}")

    return installed_apps

# --- Main Automation Logic (Auto-Click & Tab Management Implemented) ---

def semi_auto_install_and_pin(driver: webdriver.Chrome, storeId: str):

    main_window_handle = driver.current_window_handle

    # KIỂM TRA APPS ĐÃ INSTALL TRƯỚC
    installed_apps = check_installed_apps(driver, storeId)

    # Lọc ra apps cần install
    apps_to_install = [app for app in APPS if app['name'] not in installed_apps]

    if not apps_to_install:
        print("\n✅ TẤT CẢ APPS ĐÃ ĐƯỢC INSTALL! Không cần làm gì thêm.")
        return

    print(f"\n🚀 BẮT ĐẦU CÀI ĐẶT {len(apps_to_install)} APPS CÒN LẠI...")
    print("="*60)

    for app in apps_to_install:
        print(f"\n{'='*60}")
        print(f"[{app['name']}] Bắt đầu cài đặt (Type: {app['type']})...")
        print(f"{'='*60}")

        # --- VÀO THẲNG URL CỦA APP ĐỂ CÀI ĐẶT ---
        if app['type'] == 'simple':
            # TYPE 1: Apps như "flow" - Click install button ở tab của app đó
            install_url = f"https://admin.shopify.com/store/{storeId}/apps/{app['slug']}"
            print(f"[TYPE: SIMPLE] Đang vào URL: {install_url}")
            driver.get(install_url)
            delay(3)

            # TÌM VÀ CLICK TẤT CẢ INSTALL BUTTONS
            click_all_install_buttons(driver, max_attempts=3)
            delay(5)
            wait_for_admin(driver, 30)

        elif app['type'] == 'new_tab':
            # TYPE 2: Apps như "selleasy, Judge.me, nabu, dser" - Mở tab mới, tìm install button trong admin section
            print(f"[TYPE: NEW_TAB] Đang mở tab mới cho {app['name']}...")

            install_url = f"https://apps.shopify.com/{app['slug']}?shop={storeId}.myshopify.com"
            print(f"URL: {install_url}")
            driver.execute_script(f"window.open('{install_url}');")
            delay(3)

            new_window_handle = None
            for handle in driver.window_handles:
                if handle != main_window_handle:
                    new_window_handle = handle
                    break

            if not new_window_handle:
                print("❌ Không tìm thấy tab mới. Bỏ qua cài đặt.")
                continue

            driver.switch_to.window(new_window_handle)
            print("✅ Đã chuyển sang tab cài đặt ứng dụng.")

            # CHỜ PAGE LOAD XONG
            print("⏳ Đang chờ page load xong...")
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                print("✅ Page đã load xong.")
            except:
                print("⚠️ Page load timeout, nhưng vẫn tiếp tục...")

            delay(5)

            # CLICK INSTALL BUTTON LẦN 1 (Ở TAB APP)
            print(f"\n🔍 [Lần 1] Tìm install button trong tab app ({driver.current_url})...")
            install_btn_1 = find_button(driver, ["install app", "install", "add app"])

            if install_btn_1:
                try:
                    highlight_element(driver, install_btn_1)
                    print(f"✅ Tìm thấy install button lần 1. Text: '{install_btn_1.text}'. Click...")
                    driver.execute_script("arguments[0].click();", install_btn_1)
                    print(f"✅ Đã click install button lần 1.")

                    # CHỜ REDIRECT HOẶC TAB MỚI MỞ RA
                    print("⏳ Đang chờ redirect hoặc tab mới...")
                    delay(8)

                    # KIỂM TRA XEM CÓ TAB MỚI KHÔNG (admin section)
                    current_handles = driver.window_handles
                    if len(current_handles) > 2:  # Có tab mới (main + app + admin)
                        print(f"✅ Phát hiện tab mới mở ra (admin section). Đang chuyển sang tab mới nhất...")
                        # Tìm tab mới nhất
                        admin_tab = None
                        for handle in current_handles:
                            if handle != main_window_handle and handle != new_window_handle:
                                admin_tab = handle
                                break

                        if admin_tab:
                            driver.switch_to.window(admin_tab)
                            print(f"✅ Đã chuyển sang admin tab: {driver.current_url}")

                            # CHỜ PAGE LOAD XONG
                            try:
                                WebDriverWait(driver, 20).until(
                                    lambda d: d.execute_script("return document.readyState") == "complete"
                                )
                                print("✅ Admin page đã load xong.")
                            except:
                                print("⚠️ Admin page load timeout...")

                            delay(5)

                            # CLICK INSTALL BUTTON LẦN 2 (Ở ADMIN SECTION)
                            print(f"\n🔍 [Lần 2] Tìm install button trong admin section...")
                            install_btn_2 = find_button(driver, ["install app", "install", "add app"])

                            if install_btn_2:
                                try:
                                    highlight_element(driver, install_btn_2)
                                    print(f"✅ Tìm thấy install button lần 2. Text: '{install_btn_2.text}'. Click...")
                                    driver.execute_script("arguments[0].click();", install_btn_2)
                                    print(f"✅ Đã click install button lần 2 trong admin section.")
                                    delay(8)
                                except Exception as e:
                                    print(f"⚠️ Lỗi khi click install button lần 2: {e}")
                            else:
                                print(f"⚠️ Không tìm thấy install button lần 2 trong admin section.")
                                print(f"📝 Current URL: {driver.current_url}")

                            # Đóng admin tab
                            print("🔄 Đóng admin tab...")
                            driver.close()
                            driver.switch_to.window(new_window_handle)

                    else:
                        # Không có tab mới, có thể redirect trong cùng tab
                        print(f"ℹ️ Không có tab mới. URL hiện tại: {driver.current_url}")

                        # CHỜ PAGE LOAD SAU REDIRECT
                        try:
                            WebDriverWait(driver, 15).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                        except:
                            pass

                        delay(5)

                        # TÌM INSTALL BUTTON LẦN 2 (sau redirect)
                        print(f"\n🔍 [Lần 2] Tìm install button sau redirect...")
                        install_btn_2 = find_button(driver, ["install app", "install", "add app"])

                        if install_btn_2:
                            try:
                                highlight_element(driver, install_btn_2)
                                print(f"✅ Tìm thấy install button lần 2. Text: '{install_btn_2.text}'. Click...")
                                driver.execute_script("arguments[0].click();", install_btn_2)
                                print(f"✅ Đã click install button lần 2.")
                                delay(8)
                            except Exception as e:
                                print(f"⚠️ Lỗi khi click install button lần 2: {e}")
                        else:
                            print(f"⚠️ Không tìm thấy install button lần 2.")

                except Exception as e:
                    print(f"⚠️ Lỗi trong quá trình xử lý: {e}")
            else:
                print(f"⚠️ Không tìm thấy install button lần 1 trong tab app.")
                print(f"📝 Current URL: {driver.current_url}")

            # KIỂM TRA VÀ ĐÓNG TẤT CẢ TAB PHỤ
            print(f"\n🔄 Đóng tất cả tab phụ và quay về main window...")
            for handle in driver.window_handles:
                if handle != main_window_handle:
                    try:
                        driver.close()
                    except:
                        pass

            driver.switch_to.window(main_window_handle)
            print(f"✅ Đã quay về main window.")
            wait_for_admin(driver, 30)
            delay(2)

        elif app['type'] == 'modal':
            # TYPE 3: Apps như "track123, section store" - Click install button, redirect, xử lý modal
            install_url = f"https://admin.shopify.com/store/{storeId}/apps/{app['slug']}"
            print(f"[TYPE: MODAL] Đang vào URL: {install_url}")
            driver.get(install_url)
            delay(3)

            # TÌM VÀ CLICK TẤT CẢ INSTALL BUTTONS (ƯU TIÊN MODAL)
            already_installed = click_all_install_buttons(driver, max_attempts=5)

            if already_installed:
                print(f"✅ App {app['name']} đã được cài đặt sẵn.")
            else:
                print(f"✅ Hoàn tất cài đặt {app['name']}.")

            delay(5)
            wait_for_admin(driver, 30)

    print("\n" + "="*60)
    print("[Hoàn thành] Tất cả các ứng dụng đã được xử lý.")
    print("="*60)

    # KIỂM TRA LẠI SAU KHI INSTALL (FORCE RELOAD)
    print("\n🔄 KIỂM TRA LẠI SAU KHI INSTALL...")
    final_installed_apps = check_installed_apps(driver, storeId, force_reload=True)

    # Tóm tắt
    print("\n" + "="*60)
    print("📊 TỔNG KẾT CUỐI CÙNG:")
    print("="*60)
    print(f"✅ Apps đã install: {len(final_installed_apps)}/{len(APPS)}")
    for app_name in final_installed_apps:
        print(f"   ✅ {app_name}")

    not_installed = [app['name'] for app in APPS if app['name'] not in final_installed_apps]
    if not_installed:
        print(f"\n⚠️ Apps chưa install: {len(not_installed)}")
        for app_name in not_installed:
            print(f"   ❌ {app_name}")
        print(f"\n💡 Lưu ý: Vui lòng kiểm tra và install thủ công các app còn lại.")
    else:
        print(f"\n🎉 HOÀN TẤT! TẤT CẢ APPS ĐÃ ĐƯỢC INSTALL THÀNH CÔNG!")
    print("="*60)


def setup_driver() -> Optional[webdriver.Chrome]:
    """Setup và khởi tạo Chrome WebDriver với session lưu trữ"""
    try:
        print("Setting up Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        # LƯU SESSION VÀO FOLDER selenium_data
        user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selenium_data")
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Tắt các thông báo không cần thiết
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng khi khởi tạo WebDriver. Chi tiết: {e}")
        print("Vui lòng kiểm tra xem Chrome đã được cài đặt và không có phiên Selenium nào đang chạy ngầm.")
        return None

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
        delay(0.5)

        cont_btn = find_button(driver, ["Continue with email", "Tiếp tục bằng email"])
        if cont_btn:
            cont_btn.click()
            delay(2)
    except Exception:
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

def install_apps(driver: webdriver.Chrome, storeId: str):
    """Chỉ xử lý install apps (không login)"""
    semi_auto_install_and_pin(driver, storeId)
    print(f"Finished installing apps for store: {storeId}")

def setup_world_market(driver: webdriver.Chrome, storeId: str):
    """Vào markets page và setup World market với điều kiện"""
    print("\n" + "="*60)
    print("🌍 SETUP WORLD MARKET...")
    print("="*60)

    # Vào markets page
    markets_url = f"https://admin.shopify.com/store/{storeId}/markets/new"
    print(f"Đang vào trang: {markets_url}")
    driver.get(markets_url)
    delay(3)

    try:
        # 1. Tìm input field và điền "World"
        print("🔍 Tìm input field để điền 'World'...")
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.Polaris-TextField__Input"))
        )
        input_field.clear()
        input_field.send_keys("World")
        print("✅ Đã điền 'World' vào input field.")
        delay(2)

        # 2. Tìm và click button "Add condition"
        print("🔍 Tìm button 'Add condition'...")
        add_condition_btn = find_button(driver, ["Add condition"])
        if add_condition_btn:
            highlight_element(driver, add_condition_btn)
            print("✅ Tìm thấy button 'Add condition'. Click...")
            driver.execute_script("arguments[0].click();", add_condition_btn)
            delay(3)
            print("✅ Đã click 'Add condition'. Modal sẽ xuất hiện...")

            # 3. Tìm checkbox có label "Showing 237 regions" và tick vào
            print("🔍 Tìm checkbox có label 'Showing 237 regions' trong modal...")
            try:
                # Tìm element chứa text "Showing 237 regions"
                label_xpath = "//span[contains(text(), 'Showing') and contains(text(), 'regions')]"
                label_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, label_xpath))
                )
                print(f"✅ Tìm thấy label: '{label_element.text}'")

                # Tìm checkbox gần label đó (thường là parent hoặc sibling)
                # Thử tìm checkbox trong cùng row/container
                checkbox = None
                try:
                    # Cách 1: Tìm checkbox trong cùng parent
                    parent = label_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'Polaris') or contains(@class, 'row') or contains(@class, 'item')][1]")
                    checkbox = parent.find_element(By.XPATH, ".//input[@type='checkbox']")
                except:
                    try:
                        # Cách 2: Tìm checkbox trước label
                        checkbox = label_element.find_element(By.XPATH, "./preceding::input[@type='checkbox'][1]")
                    except:
                        try:
                            # Cách 3: Tìm checkbox trong cùng label tag
                            checkbox = label_element.find_element(By.XPATH, "./ancestor::label//input[@type='checkbox']")
                        except:
                            pass

                if checkbox:
                    if not checkbox.is_selected():
                        highlight_element(driver, checkbox)
                        print("✅ Tìm thấy checkbox. Đang tick vào...")
                        driver.execute_script("arguments[0].click();", checkbox)
                        delay(1)
                        print("✅ Đã tick checkbox.")
                    else:
                        print("ℹ️ Checkbox đã được tick sẵn.")
                else:
                    print("⚠️ Không tìm thấy checkbox gần label.")

            except Exception as e:
                print(f"⚠️ Không tìm thấy checkbox với label 'Showing 237 regions': {e}")
                print("🔍 Thử tìm tất cả checkboxes trong modal...")
                try:
                    all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                    print(f"📝 Tìm thấy {len(all_checkboxes)} checkboxes. Thử tick checkbox đầu tiên...")
                    if all_checkboxes:
                        first_checkbox = all_checkboxes[0]
                        if not first_checkbox.is_selected():
                            highlight_element(driver, first_checkbox)
                            driver.execute_script("arguments[0].click();", first_checkbox)
                            print("✅ Đã tick checkbox đầu tiên (fallback).")
                except Exception as e2:
                    print(f"⚠️ Lỗi khi tìm checkboxes: {e2}")

            # 4. Tìm và click button "Done"
            print("🔍 Tìm button 'Done' trong modal...")
            done_btn = find_button(driver, ["Done"])
            if done_btn:
                highlight_element(driver, done_btn)
                print("✅ Tìm thấy button 'Done'. Click...")
                driver.execute_script("arguments[0].click();", done_btn)
                delay(2)
                print("✅ Đã click 'Done'.")
            else:
                print("⚠️ Không tìm thấy button 'Done'.")
        else:
            print("⚠️ Không tìm thấy button 'Add condition'.")

        # 5. Tìm và click button "Save" có type="submit"
        click_save_button(driver)

        print("\n✅ HOÀN TẤT SETUP WORLD MARKET!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi setup World market: {e}")
        print("="*60)

def setup_contact_page(driver: webdriver.Chrome, storeId: str):
    """Setup Contact page - Đổi title từ 'Contact' thành 'Contact Us'"""
    print("\n" + "="*60)
    print("📄 SETUP CONTACT PAGE...")
    print("="*60)

    try:
        # Vào trang pages
        pages_url = f"https://admin.shopify.com/store/{storeId}/pages"
        print(f"Đang vào trang: {pages_url}")
        driver.get(pages_url)
        delay(3)

        # Tìm item element có chữ "Contact" và click vào
        print("🔍 Tìm item có chữ 'Contact'...")
        try:
            # Tìm element có text "Contact" chính xác (không phải "Contact Us")
            contact_item = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[text()='Contact'] | //span[text()='Contact'] | //div[text()='Contact'] | //button[text()='Contact']"))
            )

            highlight_element(driver, contact_item)
            print(f"✅ Tìm thấy item 'Contact'. Text: '{contact_item.text}'. Click...")
            driver.execute_script("arguments[0].click();", contact_item)
            delay(3)
            print("✅ Đã click vào item 'Contact'.")

        except Exception as e:
            print(f"⚠️ Không tìm thấy item 'Contact' bằng text chính xác: {e}")
            print("🔍 Thử tìm bằng contains...")

            # Thử tìm bằng contains (fallback)
            try:
                contact_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Contact')] | //button[contains(text(), 'Contact')] | //span[contains(text(), 'Contact')]")
                highlight_element(driver, contact_link)
                print(f"✅ Tìm thấy link/button 'Contact' (contains). Click...")
                driver.execute_script("arguments[0].click();", contact_link)
                delay(3)
                print("✅ Đã click vào 'Contact'.")
            except Exception as e2:
                print(f"❌ Không thể tìm thấy item 'Contact': {e2}")
                return

        # SAU KHI CLICK VÀO CONTACT, CHECK SAVE BUTTON MỖI 2S BẰNG CÁCH GỌI FUNCTION click_save_button
        print("🔍 Check Save button mỗi 2s sau khi vào Contact...")
        max_save_checks = 15  # Tối đa 15 lần check (30 giây)

        for check_attempt in range(max_save_checks):
            print(f"   [Attempt {check_attempt + 1}] Gọi click_save_button...")

            # Gọi function click_save_button
            save_clicked = click_save_button(driver, timeout=1)  # Timeout ngắn để check nhanh

            if save_clicked:
                print("✅ Đã click Save button thành công.")

                # SAU KHI CLICK SAVE BUTTON, QUAY LẠI TRANG PAGES VÀ TẠO PAGE "About Us"
                print("\n🔄 Quay lại trang pages để tạo page 'About Us'...")
                pages_url = f"https://admin.shopify.com/store/{storeId}/pages"
                driver.get(pages_url)
                delay(3)

                # Tìm button "Add page" và click
                print("🔍 Tìm button 'Add page'...")
                try:
                    add_page_btn = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add page')] | //a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add page')]"))
                    )

                    highlight_element(driver, add_page_btn)
                    print("✅ Tìm thấy button 'Add page'. Click...")
                    driver.execute_script("arguments[0].click();", add_page_btn)
                    delay(3)
                    print("✅ Đã click 'Add page'.")

                except Exception as e:
                    print(f"❌ Không tìm thấy button 'Add page': {e}")
                    return

                # SAU KHI CLICK ADD PAGE, CỨ 3S GỌI FUNCTION SAVE BUTTON
                print("🔍 Check Save button mỗi 3s sau khi click Add page...")
                max_save_checks = 10  # Tối đa 10 lần check (30 giây)

                for check_attempt in range(max_save_checks):
                    print(f"   [Attempt {check_attempt + 1}] Gọi click_save_button...")

                    # Gọi function click_save_button
                    save_clicked_add_page = click_save_button(driver, timeout=1)  # Timeout ngắn để check nhanh

                    if save_clicked_add_page:
                        print("✅ Tìm thấy Save button sau khi Add page. Tiếp tục điền thông tin...")

                        # Tìm input type text và điền "About Us"
                        print("🔍 Tìm input type text để điền 'About Us'...")
                        try:
                            title_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
                            )

                            highlight_element(driver, title_input)
                            print(f"✅ Tìm thấy input text. Giá trị hiện tại: '{title_input.get_attribute('value')}'")

                            # Clear và điền "About Us"
                            title_input.clear()
                            delay(0.5)
                            title_input.send_keys("About Us")
                            delay(1)
                            print("✅ Đã điền 'About Us'.")

                        except Exception as e:
                            print(f"❌ Không tìm thấy input text: {e}")

                        # Tìm radio button và click vào visible option
                        print("🔍 Tìm radio button visible...")
                        try:
                            # Tìm radio button có label chứa "visible" hoặc "published"
                            visible_radio = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@type='radio' and (@value='visible' or @value='published' or contains(following-sibling::text(), 'Visible') or contains(following-sibling::text(), 'Published'))]"))
                            )

                            highlight_element(driver, visible_radio)
                            print("✅ Tìm thấy radio button visible. Click...")
                            driver.execute_script("arguments[0].click();", visible_radio)
                            delay(1)
                            print("✅ Đã click radio button visible.")

                        except Exception as e:
                            print(f"⚠️ Không tìm thấy radio button visible: {e}")
                            # Thử tìm bằng cách khác
                            try:
                                # Tìm tất cả radio buttons và click vào cái đầu tiên
                                all_radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
                                if all_radios:
                                    highlight_element(driver, all_radios[0])
                                    driver.execute_script("arguments[0].click();", all_radios[0])
                                    print("✅ Đã click radio button đầu tiên (fallback).")
                            except Exception as e2:
                                print(f"❌ Không thể click radio button: {e2}")

                        # Click Save button cuối cùng
                        print("🔍 Click Save button cuối cùng...")
                        final_save_clicked = click_save_button(driver)
                        if final_save_clicked:
                            print("✅ Đã hoàn thành tạo About Us page!")
                        else:
                            print("⚠️ Không thể click Save button cuối cùng.")

                        return

                    # Nếu chưa click được, đợi 3s và thử lại
                    print(f"   ⏳ Chưa tìm thấy Save button enabled. Đợi 3s...")
                    delay(3)

                print("⚠️ Không tìm thấy Save button sau khi Add page trong 30s.")
                return

            # Nếu chưa click được, đợi 2s và thử lại
            print(f"   ⏳ Chưa tìm thấy Save button enabled. Đợi 2s...")
            delay(2)

        # NẾU KHÔNG CÓ SAVE BUTTON, THÔI KHÔNG LÀM GÌ THÊM
        print("⚠️ Không tìm thấy Save button enabled sau 30s. Kết thúc setup Contact page.")
        return

    except Exception as e:
        print(f"❌ Lỗi khi setup Contact page: {e}")
        print("="*60)

def setup_legal_policies(driver: webdriver.Chrome, storeId: str, policies: Dict[str, Any]):
    """Setup legal policies cho store"""
    print("\n" + "="*60)
    print("📜 SETUP LEGAL POLICIES...")
    print("="*60)

    # Danh sách các trang legal policies
    legal_pages = [
        {
            "name": "Refund Policy",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/refund",
            "policy_key": "return_and_refund"
        },
        {
            "name": "Terms of Service",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/terms-of-service",
            "policy_key": "terms_of_service"
        },
        {
            "name": "Shipping Policy",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/shipping",
            "policy_key": "shipping"
        },
        {
            "name": "Contact Information",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/contact-information",
            "policy_key": "contact_information"
        }
    ]

    try:
        for page in legal_pages:
            print(f"\n📋 Đang xử lý: {page['name']}...")
            print(f"URL: {page['url']}")

            # Vào trang policy
            driver.get(page['url'])
            delay(2)

            # Tìm button "Publish" và check aria-disabled mỗi 2s
            print(f"🔍 Tìm button 'Publish' cho {page['name']}...")

            max_attempts = 30  # Tối đa 30 lần check (60 giây)
            publish_clicked = False

            for attempt in range(max_attempts):
                try:
                    # Tìm button có text "Publish"
                    publish_btn = driver.find_element(
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'publish')]"
                    )

                    # Kiểm tra aria-disabled
                    aria_disabled = publish_btn.get_attribute("aria-disabled")

                    print(f"   [Attempt {attempt + 1}/{max_attempts}] Button 'Publish' - aria-disabled: {aria_disabled}")

                    if aria_disabled == "false":
                        # Button enabled, click vào
                        highlight_element(driver, publish_btn)
                        print(f"✅ Button 'Publish' đã enabled. Đang click...")
                        driver.execute_script("arguments[0].click();", publish_btn)
                        print(f"✅ Đã click button 'Publish' cho {page['name']}.")
                        publish_clicked = True
                        break
                    else:
                        # Button vẫn disabled, đợi 2s và thử lại
                        print(f"   ⏳ Button vẫn disabled. Đợi 2s...")
                        delay(2)

                except Exception as e:
                    if attempt == 0:
                        print(f"   ⚠️ Không tìm thấy button 'Publish': {e}")
                    delay(2)

            if not publish_clicked:
                print(f"⚠️ Không thể click button 'Publish' cho {page['name']} sau {max_attempts} lần thử.")

            # Đợi 1s trước khi chuyển sang trang tiếp theo
            delay(1)

        print("\n✅ HOÀN TẤT SETUP LEGAL POLICIES!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi setup legal policies: {e}")
        print("="*60)

def setup_shipping_zones(driver: webdriver.Chrome, storeId: str):
    """Vào trang shipping settings và thực hiện các hành động để edit International zone"""
    print("\n" + "="*60)
    print("🚚 SETUP SHIPPING ZONES...")
    print("="*60)

    try:
        # Vào trang shipping settings
        shipping_url = f"https://admin.shopify.com/store/{storeId}/settings/shipping"
        print(f"Đang vào trang: {shipping_url}")
        driver.get(shipping_url)
        delay(3)

        # Kiểm tra verification message và chờ đến khi nó biến mất
        print("🔍 Kiểm tra verification message...")
        max_verification_checks = 60  # Tối đa 60 lần check (180 giây = 3 phút)
        verification_message_found = False

        for check_attempt in range(max_verification_checks):
            try:
                # Tìm element có text "Your connection needs to be verified before you can proceed"
                verification_element = driver.find_element(
                    By.XPATH,
                    "//*[contains(text(), 'Your connection needs to be verified before you can proceed')]"
                )

                if check_attempt == 0:
                    print("⚠️ Phát hiện verification message. Đang chờ xác minh...")
                    verification_message_found = True

                print(f"   [Check {check_attempt + 1}/{max_verification_checks}] Verification message vẫn còn. Đợi 3s...")
                delay(3)

            except Exception:
                # Không tìm thấy verification message = đã xác minh xong
                if verification_message_found:
                    print("✅ Verification message đã biến mất. Tiếp tục...")
                else:
                    print("✅ Không có verification message. Tiếp tục...")
                break
        else:
            # Nếu sau max_verification_checks lần vẫn còn message
            print("⚠️ Verification message vẫn còn sau 3 phút. Tiếp tục thử...")

        # 1. Tìm element có chữ "General shipping rates" và click
        print("🔍 Tìm element có chữ 'General shipping rates'...")
        try:
            general_rates_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'General shipping rates')]"))
            )
            highlight_element(driver, general_rates_element)
            print("✅ Tìm thấy 'General shipping rates'. Click...")
            driver.execute_script("arguments[0].click();", general_rates_element)
            delay(2)
            print("✅ Đã click 'General shipping rates'.")

            # 2. Tìm button thứ 2 với aria-label="More actions" và click
            print("🔍 Tìm button thứ 2 với aria-label='More actions'...")
            try:
                more_actions_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[2]"))
                )
                highlight_element(driver, more_actions_btn)
                print("✅ Tìm thấy button 'More actions' thứ 2. Click...")
                driver.execute_script("arguments[0].click();", more_actions_btn)
                delay(2)
                print("✅ Đã click 'More actions' thứ 2.")

                # 2a. Chờ menu 'Polaris-Popover__Content' xuất hiện và tìm 'Edit zone'
                print("🔍 Chờ menu 'Polaris-Popover__Content' xuất hiện...")
                try:
                    menu = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                    )
                    print("✅ Menu đã xuất hiện.")

                    # 2b. Tìm element có chữ "Edit rate" trong menu
                    edit_zone_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Edit rate')]")
                    highlight_element(driver, edit_zone_element)
                    print("✅ Tìm thấy 'Edit rate'. Click...")
                    driver.execute_script("arguments[0].click();", edit_zone_element)
                    delay(2)
                    print("✅ Đã click 'Edit rate'.")

                    # 2c. Chờ modal xuất hiện sau khi click "Edit rate"
                    print("🔍 Chờ modal xuất hiện...")
                    try:
                        modal = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                        )
                        print("✅ Modal đã xuất hiện.")
                        delay(1)

                        # 2d. Tìm select element và chọn option đầu tiên
                        print("🔍 Tìm select element và chọn option đầu tiên...")
                        try:
                            select_element = modal.find_element(By.TAG_NAME, "select")
                            highlight_element(driver, select_element)
                            print("✅ Tìm thấy select element.")

                            # Lấy tất cả options và chọn option đầu tiên
                            options = select_element.find_elements(By.TAG_NAME, "option")
                            if options:
                                print(f"✅ Tìm thấy {len(options)} options. Chọn option đầu tiên...")
                                driver.execute_script("arguments[0].selectedIndex = 0; arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_element)
                                delay(1)
                                print("✅ Đã chọn option đầu tiên.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy select element: {e}")

                        # 2e. Tìm input name="amount" và sửa thành "9.99"
                        print("🔍 Tìm input name='amount' và sửa thành '9.99'...")
                        try:
                            amount_input = modal.find_element(By.CSS_SELECTOR, "input[name='amount']")
                            highlight_element(driver, amount_input)
                            print("✅ Tìm thấy input name='amount'.")

                            # Clear input trước
                            amount_input.clear()
                            delay(0.5)
                            # Xóa giá trị cũ bằng JavaScript (để chắc chắn)
                            driver.execute_script("arguments[0].value = '';", amount_input)
                            delay(0.5)
                            # Nhập giá trị mới
                            amount_input.send_keys("9.99")
                            delay(1)
                            print("✅ Đã sửa giá trị thành '9.99'.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy input name='amount': {e}")

                        # 2f. Tìm và click element "Remove conditional pricing"
                        print("🔍 Tìm element 'Remove conditional pricing' và click...")
                        try:
                            remove_conditional = modal.find_element(By.XPATH, ".//*[contains(text(), 'Remove conditional pricing')]")
                            highlight_element(driver, remove_conditional)
                            print("✅ Tìm thấy 'Remove conditional pricing'. Click...")
                            driver.execute_script("arguments[0].click();", remove_conditional)
                            delay(1)
                            print("✅ Đã click 'Remove conditional pricing'.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy 'Remove conditional pricing': {e}")

                        # 2j. Tìm và click button "Done"
                        print("🔍 Tìm button 'Done' và click...")
                        done_button = None
                        try:
                            # Cách 1: Tìm button có text "Done" trực tiếp
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[contains(text(), 'Done')]")
                                print("✅ Tìm thấy button 'Done' (cách 1: text trực tiếp)")
                            except:
                                pass

                            # Cách 2: Tìm button có descendant chứa text "Done"
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[.//*[contains(text(), 'Done')]]")
                                    print("✅ Tìm thấy button 'Done' (cách 2: text trong descendant)")
                                except:
                                    pass

                            # Cách 3: Tìm button có normalize-space text = "Done"
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[normalize-space()='Done' or .//*[normalize-space()='Done']]")
                                    print("✅ Tìm thấy button 'Done' (cách 3: normalize-space)")
                                except:
                                    pass

                            # Cách 4: Tìm button có text chứa "Done" (case-insensitive)
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[contains(translate(., 'DONE', 'done'), 'done') or .//*[contains(translate(., 'DONE', 'done'), 'done')]]")
                                    print("✅ Tìm thấy button 'Done' (cách 4: case-insensitive)")
                                except:
                                    pass

                            # Cách 5: Tìm tất cả buttons trong modal và kiểm tra text
                            if not done_button:
                                try:
                                    all_buttons = modal.find_elements(By.XPATH, ".//button")
                                    print(f"📝 Tìm thấy {len(all_buttons)} buttons trong modal. Đang kiểm tra...")
                                    for btn in all_buttons:
                                        btn_text = btn.text.strip().lower()
                                        if 'done' in btn_text:
                                            done_button = btn
                                            print(f"✅ Tìm thấy button 'Done' (cách 5: quét tất cả buttons). Text: '{btn.text}'")
                                            break
                                except Exception as e:
                                    print(f"⚠️ Lỗi khi quét buttons: {e}")

                            # Click button nếu tìm thấy
                            if done_button:
                                highlight_element(driver, done_button)
                                print(f"✅ Tìm thấy button 'Done'. Text hiển thị: '{done_button.text}'. Click...")
                                driver.execute_script("arguments[0].click();", done_button)
                                delay(2)
                                print("✅ Đã click button 'Done'.")

                                # Chờ modal đóng lại trước khi tiếp tục step #3
                                print("🔍 Đang chờ modal đóng lại...")
                                try:
                                    WebDriverWait(driver, 10).until(
                                        EC.invisibility_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                                    )
                                    print("✅ Modal đã đóng lại.")
                                    delay(1)
                                except Exception as e:
                                    print(f"⚠️ Không thể xác nhận modal đã đóng: {e}")
                                    delay(3)  # Đợi thêm 3 giây để chắc chắn
                            else:
                                print("⚠️ Không tìm thấy button 'Done' sau khi thử tất cả các phương pháp.")
                                # Debug: In ra tất cả buttons trong modal
                                try:
                                    all_buttons = modal.find_elements(By.TAG_NAME, "button")
                                    print(f"📝 DEBUG - Danh sách tất cả buttons trong modal ({len(all_buttons)} buttons):")
                                    for i, btn in enumerate(all_buttons):
                                        print(f"   Button {i+1}: Text='{btn.text}' | Visible={btn.is_displayed()}")
                                except:
                                    pass

                        except Exception as e:
                            print(f"⚠️ Lỗi khi tìm button 'Done': {e}")

                    except Exception as e:
                        print(f"⚠️ Không tìm thấy modal hoặc lỗi khi xử lý modal: {e}")

                except Exception as e:
                    print(f"⚠️ Không tìm thấy menu hoặc 'Edit rate': {e}")
            except Exception as e:
                print(f"⚠️ Không tìm thấy button 'More actions': {e}")

            # 3. Tìm button thứ 3 với aria-label="More actions" và click
            print("🔍 Tìm button thứ 3 với aria-label='More actions'...")
            try:
                more_actions_btn_3 = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[3]"))
                )
                highlight_element(driver, more_actions_btn_3)
                print("✅ Tìm thấy button 'More actions' thứ 3. Click...")
                driver.execute_script("arguments[0].click();", more_actions_btn_3)
                delay(2)
                print("✅ Đã click 'More actions' thứ 3.")

                # 3a. Chờ menu 'Polaris-Popover__Content' xuất hiện và tìm 'Edit zone'
                print("🔍 Chờ menu 'Polaris-Popover__Content' xuất hiện...")
                try:
                    menu = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                    )
                    print("✅ Menu đã xuất hiện.")

                    # 3b. Tìm element có chữ "Edit rate" trong menu
                    edit_zone_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Edit rate')]")
                    highlight_element(driver, edit_zone_element)
                    print("✅ Tìm thấy 'Edit rate'. Click...")
                    driver.execute_script("arguments[0].click();", edit_zone_element)
                    delay(2)
                    print("✅ Đã click 'Edit rate'.")

                    # 3c. Chờ modal xuất hiện sau khi click "Edit rate"
                    print("🔍 Chờ modal xuất hiện...")
                    try:
                        modal = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                        )
                        print("✅ Modal đã xuất hiện.")
                        delay(1)

                        # 3d. Tìm select element và chọn option thứ 2
                        print("🔍 Tìm select element và chọn option thứ 2...")
                        try:
                            select_element = modal.find_element(By.TAG_NAME, "select")
                            highlight_element(driver, select_element)
                            print("✅ Tìm thấy select element.")

                            # Lấy tất cả options và chọn option thứ 2
                            options = select_element.find_elements(By.TAG_NAME, "option")
                            if len(options) >= 2:
                                print(f"✅ Tìm thấy {len(options)} options. Chọn option thứ 2...")
                                driver.execute_script("arguments[0].selectedIndex = 1; arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_element)
                                delay(1)
                                print("✅ Đã chọn option thứ 2.")
                            else:
                                print(f"⚠️ Chỉ có {len(options)} option(s), không đủ để chọn option thứ 2.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy select element: {e}")

                        # 3e. Tìm input name="amount" và sửa thành "0.00"
                        print("🔍 Tìm input name='amount' và sửa thành '0.00'...")
                        try:
                            amount_input = modal.find_element(By.CSS_SELECTOR, "input[name='amount']")
                            highlight_element(driver, amount_input)
                            print("✅ Tìm thấy input name='amount'.")

                            # Clear input trước
                            amount_input.clear()
                            delay(0.5)
                            # Xóa giá trị cũ bằng JavaScript (để chắc chắn)
                            driver.execute_script("arguments[0].value = '';", amount_input)
                            delay(0.5)
                            # Nhập giá trị mới
                            amount_input.send_keys("0.00")
                            delay(1)
                            print("✅ Đã sửa giá trị thành '0.00'.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy input name='amount': {e}")

                        # 3f. Tìm và click element "Remove conditional pricing"
                        print("🔍 Tìm element 'Remove conditional pricing' và click...")
                        try:
                            remove_conditional = modal.find_element(By.XPATH, ".//*[contains(text(), 'Remove conditional pricing')]")
                            highlight_element(driver, remove_conditional)
                            print("✅ Tìm thấy 'Remove conditional pricing'. Click...")
                            driver.execute_script("arguments[0].click();", remove_conditional)
                            delay(1)
                            print("✅ Đã click 'Remove conditional pricing'.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy 'Remove conditional pricing': {e}")

                        # 3j. Tìm và click button "Done"
                        print("🔍 Tìm button 'Done' và click...")
                        done_button = None
                        try:
                            # Cách 1: Tìm button có text "Done" trực tiếp
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[contains(text(), 'Done')]")
                                print("✅ Tìm thấy button 'Done' (cách 1: text trực tiếp)")
                            except:
                                pass

                            # Cách 2: Tìm button có descendant chứa text "Done"
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[.//*[contains(text(), 'Done')]]")
                                    print("✅ Tìm thấy button 'Done' (cách 2: text trong descendant)")
                                except:
                                    pass

                            # Cách 3: Tìm button có normalize-space text = "Done"
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[normalize-space()='Done' or .//*[normalize-space()='Done']]")
                                    print("✅ Tìm thấy button 'Done' (cách 3: normalize-space)")
                                except:
                                    pass

                            # Cách 4: Tìm button có text chứa "Done" (case-insensitive)
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[contains(translate(., 'DONE', 'done'), 'done') or .//*[contains(translate(., 'DONE', 'done'), 'done')]]")
                                    print("✅ Tìm thấy button 'Done' (cách 4: case-insensitive)")
                                except:
                                    pass

                            # Cách 5: Tìm tất cả buttons trong modal và kiểm tra text
                            if not done_button:
                                try:
                                    all_buttons = modal.find_elements(By.XPATH, ".//button")
                                    print(f"📝 Tìm thấy {len(all_buttons)} buttons trong modal. Đang kiểm tra...")
                                    for btn in all_buttons:
                                        btn_text = btn.text.strip().lower()
                                        if 'done' in btn_text:
                                            done_button = btn
                                            print(f"✅ Tìm thấy button 'Done' (cách 5: quét tất cả buttons). Text: '{btn.text}'")
                                            break
                                except Exception as e:
                                    print(f"⚠️ Lỗi khi quét buttons: {e}")

                            # Click button nếu tìm thấy
                            if done_button:
                                highlight_element(driver, done_button)
                                print(f"✅ Tìm thấy button 'Done'. Text hiển thị: '{done_button.text}'. Click...")
                                driver.execute_script("arguments[0].click();", done_button)
                                delay(2)
                                print("✅ Đã click button 'Done'.")
                            else:
                                print("⚠️ Không tìm thấy button 'Done' sau khi thử tất cả các phương pháp.")
                                # Debug: In ra tất cả buttons trong modal
                                try:
                                    all_buttons = modal.find_elements(By.TAG_NAME, "button")
                                    print(f"📝 DEBUG - Danh sách tất cả buttons trong modal ({len(all_buttons)} buttons):")
                                    for i, btn in enumerate(all_buttons):
                                        print(f"   Button {i+1}: Text='{btn.text}' | Visible={btn.is_displayed()}")
                                except:
                                    pass

                        except Exception as e:
                            print(f"⚠️ Lỗi khi tìm button 'Done': {e}")

                    except Exception as e:
                        print(f"⚠️ Không tìm thấy modal hoặc lỗi khi xử lý modal: {e}")

                except Exception as e:
                    print(f"⚠️ Không tìm thấy menu hoặc 'Edit rate': {e}")
            except Exception as e:
                print(f"⚠️ Không tìm thấy button 'More actions' thứ 3: {e}")

            # Sau step #3, tìm TẤT CẢ các button từ thứ 4 trở đi với aria-label="More actions" và delete
            print("\n🔍 Tìm tất cả các button 'More actions' từ thứ 4 trở đi để delete...")

            # Tìm tất cả buttons có aria-label="More actions"
            try:
                all_more_actions_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='More actions']")
                total_buttons = len(all_more_actions_buttons)
                print(f"✅ Tìm thấy tổng cộng {total_buttons} buttons 'More actions'.")

                # Delete từ button thứ 4 trở đi (index 3 trở đi)
                buttons_to_delete = total_buttons - 3  # Bỏ qua 3 button đầu tiên

                if buttons_to_delete > 0:
                    print(f"📝 Sẽ delete button(s) (BỎ QUA button thứ 7 - International)...")

                    # Phase 1: Delete buttons 4, 5, 6 (cho đến khi gặp International)
                    # LƯU Ý: Luôn delete button thứ 4 vì sau mỗi lần delete, index sẽ thay đổi
                    deleted_count = 0
                    for attempt in range(buttons_to_delete):
                        print(f"\n🔍 Phase 1 - Attempt {attempt + 1}: Tìm button 'More actions' thứ 4...")
                        try:
                            # Luôn tìm button thứ 4 vì sau mỗi lần delete, các button sau sẽ dịch lên
                            more_actions_btn = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[4]"))
                            )

                            # Kiểm tra xem button này có nằm trong div có chữ "International" không
                            is_international = False
                            try:
                                parent_div = more_actions_btn.find_element(By.XPATH, "./ancestor::div[.//*[contains(text(), 'International')]]")
                                is_international = True
                                print("⚠️ Button thứ 4 nằm trong div 'International'. Bỏ qua không delete.")
                            except:
                                # Không tìm thấy "International" trong parent -> OK để delete
                                pass

                            if is_international:
                                # Đã gặp International, dừng Phase 1
                                print("✅ Phase 1 hoàn tất - Đã gặp International button.")
                                break

                            highlight_element(driver, more_actions_btn)
                            print(f"✅ Tìm thấy button 'More actions' thứ 4. Click...")
                            driver.execute_script("arguments[0].click();", more_actions_btn)
                            delay(2)

                            # Chờ menu 'Polaris-Popover__Content' xuất hiện và tìm 'Delete'
                            print("🔍 Chờ menu 'Polaris-Popover__Content' xuất hiện...")
                            try:
                                menu = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                                )
                                print("✅ Menu đã xuất hiện.")

                                # Tìm element có chữ "Delete" trong menu
                                delete_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Delete')]")
                                highlight_element(driver, delete_element)
                                print("✅ Tìm thấy 'Delete'. Click...")
                                driver.execute_script("arguments[0].click();", delete_element)
                                delay(2)
                                deleted_count += 1
                                print(f"✅ Đã delete button (Phase 1 - deleted {deleted_count}).")

                            except Exception as e:
                                print(f"⚠️ Không tìm thấy menu hoặc 'Delete': {e}")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy button 'More actions' thứ 4: {e}")
                            print("� Có thể đã delete hết các buttons. Kết thúc loop.")
                            break

                    print(f"\n✅ Phase 1 hoàn tất - Đã delete {deleted_count} button(s).")

                    # Phase 2: Delete buttons từ thứ 5 trở đi (bỏ qua button thứ 4 - International)
                    print(f"\n📝 Phase 2: Bỏ qua button thứ 4 (International), delete từ button thứ 5 trở đi...")

                    # Đếm lại số buttons còn lại
                    all_more_actions_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='More actions']")
                    remaining_buttons = len(all_more_actions_buttons)
                    print(f"✅ Còn lại {remaining_buttons} buttons 'More actions'.")

                    # Delete từ button thứ 5 trở đi (bỏ qua button 1, 2, 3, 4)
                    buttons_to_delete_phase2 = remaining_buttons - 4  # Bỏ qua 4 buttons đầu

                    if buttons_to_delete_phase2 > 0:
                        print(f"📝 Sẽ delete {buttons_to_delete_phase2} button(s) nữa (từ button thứ 5)...")
                        phase2_deleted = 0

                        for i in range(buttons_to_delete_phase2):
                            print(f"\n🔍 Phase 2 - Attempt {i+1}: Delete button thứ 5...")
                            try:
                                more_actions_btn = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[5]"))
                                )
                                highlight_element(driver, more_actions_btn)
                                print(f"✅ Tìm thấy button 'More actions' thứ 5. Click...")
                                driver.execute_script("arguments[0].click();", more_actions_btn)
                                delay(2)

                                # Chờ menu và click Delete
                                print("🔍 Chờ menu xuất hiện...")
                                try:
                                    menu = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                                    )
                                    delete_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Delete')]")
                                    highlight_element(driver, delete_element)
                                    print("✅ Click 'Delete'...")
                                    driver.execute_script("arguments[0].click();", delete_element)
                                    delay(2)
                                    phase2_deleted += 1
                                    print(f"✅ Đã delete button (Phase 2 - deleted {phase2_deleted}).")
                                except Exception as e:
                                    print(f"⚠️ Không tìm thấy menu hoặc 'Delete': {e}")

                            except Exception as e:
                                print(f"⚠️ Không tìm thấy button 'More actions' thứ 5: {e}")
                                break

                        print(f"\n✅ Phase 2 hoàn tất - Đã delete {phase2_deleted} button(s).")
                        print(f"\n✅ Tổng cộng đã delete {deleted_count + phase2_deleted} button(s).")
                    else:
                        print("ℹ️  Không có button nào để delete ở Phase 2.")
                        print(f"\n✅ Tổng cộng đã delete {deleted_count} button(s).")

                else:
                    print("ℹ️  Không có button nào cần delete (chỉ có 3 buttons hoặc ít hơn).")

            except Exception as e:
                print(f"⚠️ Lỗi khi tìm các buttons 'More actions': {e}")

            # Sau khi hoàn thành tất cả các delete, gọi hàm click_save_button
            print("\n🔍 Kiểm tra và click button 'Save' nếu có...")
            click_save_button(driver)

        except Exception as e:
            print(f"⚠️ Không tìm thấy element 'General shipping rates': {e}")
            return

    except Exception as e:
        print(f"❌ Lỗi khi setup shipping zones: {e}")
        print("="*60)

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

def upload_favicon(driver: webdriver.Chrome, storeId: str):
    """Vào trang online store preferences và upload favicon (aaa.png từ Downloads folder)"""
    print("\n" + "="*60)
    print("🖼️ UPLOAD FAVICON...")
    print("="*60)

    try:
        # Vào trang online store preferences
        preferences_url = f"https://admin.shopify.com/store/{storeId}/online_store/preferences"
        print(f"Đang vào trang: {preferences_url}")
        driver.get(preferences_url)
        delay(3)

        # Tìm input có id=":re:" và textarea có id=":rf:"
        print("🔍 Kiểm tra input và textarea...")
        wait = WebDriverWait(driver, 15)

        try:
            # Tìm input với id=":re:"
            print("🔍 Đang tìm input với id=':re:'...")
            input_element = wait.until(
                EC.presence_of_element_located((By.ID, ":re:"))
            )
            print(f"✅ Tìm thấy input với id=':re:'")

            # Tìm textarea với id=":rf:"
            print("🔍 Đang tìm textarea với id=':rf:'...")
            textarea_element = wait.until(
                EC.presence_of_element_located((By.ID, ":rf:"))
            )
            print(f"✅ Tìm thấy textarea với id=':rf:'")

            # Lấy giá trị của input và textarea
            input_value = input_element.get_attribute("value")
            textarea_value = textarea_element.get_attribute("value")

            print(f"\n📝 Input value: '{input_value}'")
            print(f"📝 Textarea value: '{textarea_value}'")

            # Kiểm tra cả 2 đều có value (không rỗng)
            if input_value and input_value.strip() and textarea_value and textarea_value.strip():
                print("✅ Cả 2 fields đều có value. Bắt đầu check Save button mỗi 2s...")

                # Cứ 2s check save button 1 lần
                max_checks = 30  # Tối đa 30 lần check (60 giây)
                for check_attempt in range(max_checks):
                    print(f"   [Attempt {check_attempt + 1}/{max_checks}] Gọi click_save_button...")

                    # Gọi function click_save_button
                    save_clicked = click_save_button(driver, timeout=1)  # Timeout ngắn để check nhanh

                    if save_clicked:
                        print("✅ Đã click Save button thành công.")
                        break
                    else:
                        print(f"   ⏳ Save button chưa enabled. Đợi 2s...")
                        delay(2)

                if not save_clicked:
                    print("⚠️ Không thể click Save button sau 60s.")
            else:
                print("⚠️ Một hoặc cả 2 fields đều chưa có value.")
                if not (input_value and input_value.strip()):
                    print(f"   - Input trống")
                if not (textarea_value and textarea_value.strip()):
                    print(f"   - Textarea trống")

        except Exception as e:
            print(f"❌ Lỗi khi tìm input/textarea: {e}")
            import traceback
            traceback.print_exc()

        print("\n✅ HOÀN TẤT UPLOAD FAVICON!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi upload favicon: {e}")
        print("="*60)

def import_theme(driver: webdriver.Chrome, storeId: str):
    """Vào trang themes và thực hiện import theme bằng cách click Import theme (data-state="closed") rồi Upload zip file trong menu (data-state="open")"""
    print("\n" + "="*60)
    print("🎨 IMPORT THEME...")
    print("="*60)

    try:
        # Vào trang themes
        themes_url = f"https://admin.shopify.com/store/{storeId}/themes"
        print(f"Đang vào trang: {themes_url}")
        driver.get(themes_url)
        delay(3)

        # Tìm và click element "Import theme" có data-state="closed"
        print("🔍 Tìm element 'Import theme' với data-state='closed'...")
        wait = WebDriverWait(driver, 10)
        import_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@data-state='closed']//div[@class='Polaris-ActionMenu-Actions__ActionsLayout']//div//span[@class='Polaris-Text--root Polaris-Text--bodySm Polaris-Text--medium'][normalize-space()='Import theme']"
            ))
        )
        highlight_element(driver, import_button)
        print("✅ Tìm thấy 'Import theme' với data-state='closed'. Click...")
        driver.execute_script("arguments[0].click();", import_button)
        delay(2)
        print("✅ Đã click 'Import theme'.")

        # Chờ menu hiện ra với data-state="open" và tìm element "Upload zip file"
        print("🔍 Chờ menu với data-state='open' và tìm 'Upload zip file'...")
        upload_zip = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@data-state='open']//span[contains(text(),'Upload zip file')]"
            ))
        )
        highlight_element(driver, upload_zip)
        print("✅ Tìm thấy 'Upload zip file' trong menu data-state='open'. Click...")
        driver.execute_script("arguments[0].click();", upload_zip)
        delay(2)
        print("✅ Đã click 'Upload zip file'.")

        print("\n✅ HOÀN TẤT IMPORT THEME!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi import theme: {e}")
        print("="*60)


def show_interactive_menu():
    """Hiển thị menu interactive để chọn các functions muốn chạy"""
    print("\n" + "="*80)
    print("🎯 CHỌN CÁC TASKS BẠN MUỐN CHẠY")
    print("="*80)
    print("📌 Sử dụng phím ↑/↓ để di chuyển")
    print("📌 Nhấn SPACE để chọn/bỏ chọn")
    print("📌 Nhấn ENTER để xác nhận và chạy")
    print("="*80 + "\n")

    # Định nghĩa các options
    task_options = [
        ('install_apps', '📦 Cài đặt Apps'),
        ('handle_dser_open_and_confirm', '🛠️  Xử lý DSers Open & Confirm'),
        ('setup_world_market', '🌍 Cài đặt World Market'),
        ('setup_legal_policies', '📜 Cài đặt Legal Policies'),
        ('setup_contact_page', '📄 Cài đặt Contact Page'),
        ('setup_shipping_zones', '🚚 Cài đặt Shipping Zones'),
    ]

    # Tạo câu hỏi checkbox
    questions = [
        inquirer.Checkbox(
            'tasks',
            message="Chọn các tasks bạn muốn chạy",
            choices=[label for _, label in task_options],
            default=[]  # Không chọn mặc định, để trống
        ),
    ]

    # Hiển thị menu và lấy kết quả
    try:
        answers = inquirer.prompt(questions)
        if not answers or not answers['tasks']:
            print("\n⚠️  Không có task nào được chọn. Thoát chương trình.")
            return []

        # Map labels trở lại function names
        selected_labels = set(answers['tasks'])
        selected_tasks = [func_name for func_name, label in task_options if label in selected_labels]

        print(f"\n✅ Đã chọn {len(selected_tasks)} task(s):")
        for task in selected_tasks:
            print(f"   - {task}")
        print()

        return selected_tasks
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi người dùng. Thoát chương trình.")
        return []


def main():
    """Main execution function"""
    # Load credentials (chỉ một object duy nhất)
    entry = load_credentials()
    if not entry:
        print("No valid credentials found. Exiting.")
        return

    email, password, storeId = entry["email"], entry["password"], entry["storeId"]

    print(f"\n{'='*60}")
    print(f"📌 SỬ DỤNG STORE: {storeId}")
    print(f"📌 EMAIL: {email}")
    print(f"{'='*60}\n")

    # Hiển thị menu để chọn tasks
    selected_tasks = show_interactive_menu()
    if not selected_tasks:
        return

    # Setup WebDriver
    driver = setup_driver()
    if not driver:
        return

    try:
        # BƯỚC 1: LOGIN (luôn chạy)
        print("\n🔐 BƯỚC 1: ĐĂNG NHẬP VÀO SHOPIFY...")
        print("="*60)
        logged = login_to_shopify(driver, email, password, storeId)

        if not logged:
            print("🚫 Cannot proceed. Login failed.")
            return

        print("\n✅ ĐĂNG NHẬP THÀNH CÔNG!")
        print("="*60)

        # Chạy các tasks đã chọn
        if 'install_apps' in selected_tasks:
            print("\n📦 BƯỚC 2: CÀI ĐẶT APPS...")
            print("="*60)
            install_apps(driver, storeId)

        if 'handle_dser_open_and_confirm' in selected_tasks:
            print("\n🛠️ BƯỚC 3: XỬ LÝ DSERS OPEN VÀ CONFIRM...")
            print("="*60)
            handle_dser_open_and_confirm(driver, storeId)

        if 'setup_world_market' in selected_tasks:
            print("\n🌍 BƯỚC 4: CÀI ĐẶT WORLD MARKET...")
            print("="*60)
            setup_world_market(driver, storeId)

        if 'setup_legal_policies' in selected_tasks:
            print("\n📜 BƯỚC 5: CÀI ĐẶT LEGAL POLICIES...")
            print("="*60)
            setup_legal_policies(driver, storeId, entry.get("policies", {}))

        if 'setup_contact_page' in selected_tasks:
            print("\n📄 BƯỚC 6: CÀI ĐẶT CONTACT PAGE...")
            print("="*60)
            setup_contact_page(driver, storeId)

        if 'setup_shipping_zones' in selected_tasks:
            print("\n🚚 BƯỚC 7: CÀI ĐẶT SHIPPING ZONES...")
            print("="*60)
            setup_shipping_zones(driver, storeId)

    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
    finally:
        # ⚠️ GIỮ BROWSER MỞ - Chờ user xác nhận trước khi đóng
        print("\n" + "="*80)
        print("✅ [Hoàn thành] Tất cả các tác vụ đã hoàn tất.")
        print("📌 Browser sẽ VẪN MỞ để bạn kiểm tra kết quả.")
        print("🔴 Nhấn Enter ở đây khi bạn MUỐN ĐÓNG browser...")
        print("="*80)
        input()

        try:
            driver.quit()
            print("✅ Browser đã được đóng thành công.")
        except:
            print("⚠️ Browser có thể đã được đóng thủ công.")

if __name__ == "__main__":
    main()