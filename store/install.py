from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List
from utils.element import delay, wait_for_admin, highlight_element, find_button

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

def semi_auto_install_and_pin(driver: webdriver.Chrome, storeId: str, should_stop_callback=None):

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
        # Check stop flag trước khi cài mỗi app
        if should_stop_callback and should_stop_callback():
            print("\n⏹️ DỪNG TASK - User đã nhấn Stop button")
            return
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

def install_apps(driver: webdriver.Chrome, storeId: str, should_stop_callback=None):
    semi_auto_install_and_pin(driver, storeId, should_stop_callback)
    print(f"Finished installing apps for store: {storeId}")