# file này mới nhất chưa push

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element, click_save_button, find_iframe_with_element, load_credentials
import os


def setup_preferences(driver: webdriver.Chrome, storeId: str):
    """Vào trang online store preferences và điền thông tin Name và Description"""
    print("\n" + "="*60)
    print("⚙️  SETUP PREFERENCES...")
    print("="*60)

    # Load credentials để lấy seo.title và seo.description
    entry = load_credentials()
    seo_title = entry.get("seo", {}).get("title", "")
    seo_description = entry.get("seo", {}).get("description", "")

    if not seo_title or not seo_description:
        print("⚠️ Không tìm thấy seo.title hoặc seo.description trong data.json")
        return

    print(f"📝 SEO Title: {seo_title}")
    print(f"📝 SEO Description: {seo_description}")

    try:
        # Vào trang online store preferences
        preferences_url = f"https://admin.shopify.com/store/{storeId}/online_store/preferences"
        print(f"Đang vào trang: {preferences_url}")
        driver.get(preferences_url)

        # Đợi page load hoàn toàn
        print("⏳ Đang chờ page load...")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        delay(15)  # Đợi thêm 15 giây cho JS load hoàn toàn

        # Scroll xuống để đảm bảo elements hiển thị
        print("📜 Scroll xuống để load elements...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        delay(2)
        driver.execute_script("window.scrollTo(0, 0);")
        delay(2)

        print("✅ Page đã load xong, bắt đầu tìm iframes...")

        # TÌM VÀ SWITCH VÀO IFRAME (sử dụng utility function)
        iframe_switched = find_iframe_with_element(driver, ":r5:")

        if not iframe_switched:
            print("⚠️ Không tìm thấy input trong bất kỳ iframe nào. Thử tìm ở main page...")

        # Tìm input Name bằng ID
        print("\n🔍 Tìm input Name bằng ID ':r5:'...")
        try:
            # Đợi element hiển thị và có thể tương tác
            name_input = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, ":r5:"))
            )
            highlight_element(driver, name_input)
            print(f"✅ Tìm thấy input Name. Giá trị hiện tại: '{name_input.get_attribute('value')}'")

            # Focus vào input trước
            driver.execute_script("arguments[0].focus();", name_input)
            delay(0.3)

            # Click vào input để focus
            driver.execute_script("arguments[0].click();", name_input)
            delay(0.5)

            # Clear và điền giá trị từ seo.title
            driver.execute_script("arguments[0].value = '';", name_input)
            delay(0.3)
            driver.execute_script(f"arguments[0].value = '{seo_title}';", name_input)

            # Trigger events để React nhận biết thay đổi
            driver.execute_script("""
                var event = new Event('input', { bubbles: true });
                arguments[0].dispatchEvent(event);
                var changeEvent = new Event('change', { bubbles: true });
                arguments[0].dispatchEvent(changeEvent);
            """, name_input)
            delay(1)
            print(f"✅ Đã điền '{seo_title}' vào input Name.")
        except Exception as e:
            print(f"❌ Không tìm thấy input Name với ID ':r5:': {e}")

        # Tìm textarea Description bằng ID
        print("\n🔍 Tìm textarea Description bằng ID ':r6:'...")
        try:
            # Đợi element hiển thị và có thể tương tác
            desc_textarea = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, ":r6:"))
            )
            highlight_element(driver, desc_textarea)
            print(f"✅ Tìm thấy textarea Description. Giá trị hiện tại: '{desc_textarea.get_attribute('value')}'")

            # Focus vào textarea trước
            driver.execute_script("arguments[0].focus();", desc_textarea)
            delay(0.3)

            # Click vào textarea để focus
            driver.execute_script("arguments[0].click();", desc_textarea)
            delay(0.5)

            # Clear và điền giá trị từ seo.description
            driver.execute_script("arguments[0].value = '';", desc_textarea)
            delay(0.3)
            driver.execute_script(f"arguments[0].value = '{seo_description}';", desc_textarea)

            # Trigger events để React nhận biết thay đổi
            driver.execute_script("""
                var event = new Event('input', { bubbles: true });
                arguments[0].dispatchEvent(event);
                var changeEvent = new Event('change', { bubbles: true });
                arguments[0].dispatchEvent(changeEvent);
            """, desc_textarea)
            delay(1)
            print(f"✅ Đã điền '{seo_description}' vào textarea Description.")
        except Exception as e:
            print(f"❌ Không tìm thấy textarea Description với ID ':r6:': {e}")

        # Tìm button upload và upload file aa.png
        print("\n🔍 Tìm button upload file...")
        try:
            upload_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/form[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/button[1]"))
            )
            highlight_element(driver, upload_button)
            print("✅ Tìm thấy button upload.")

            # Tìm input file (thường ẩn) - có thể trong cùng container với button
            print("🔍 Tìm input type='file'...")
            try:
                # Thử tìm input file gần button upload
                file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                print("✅ Tìm thấy input file")

                # Lấy đường dẫn đến file aa.png trong Downloads
                import os
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "aaa.png")
                print(f"📁 File path: {downloads_path}")

                # Kiểm tra file có tồn tại không
                if os.path.exists(downloads_path):
                    print(f"✅ File tồn tại: {downloads_path}")

                    # Upload file bằng cách send_keys vào input file
                    file_input.send_keys(downloads_path)
                    delay(2)
                    print("✅ Đã upload file aa.png thành công!")
                else:
                    print(f"❌ File không tồn tại: {downloads_path}")
                    print("⚠️ Vui lòng đảm bảo file aa.png có trong thư mục Downloads")

            except Exception as e:
                print(f"⚠️ Không tìm thấy input file: {e}")
                print("🔄 Thử click vào button để mở file picker...")
                try:
                    driver.execute_script("arguments[0].click();", upload_button)
                    delay(2)
                    print("✅ Đã click vào button upload. Vui lòng chọn file thủ công nếu cần.")
                except Exception as e2:
                    print(f"❌ Không thể click button upload: {e2}")

        except Exception as e:
            print(f"❌ Không tìm thấy button upload: {e}")

        # Switch về main content trước khi click Save
        print("\n🔄 Switch về main content...")
        driver.switch_to.default_content()
        delay(1)

        # Click Save button
        print("🔍 Click Save button...")
        save_clicked = click_save_button(driver)
        if save_clicked:
            print("✅ Đã click Save button thành công.")
        else:
            print("⚠️ Không thể click Save button.")

        print("\n✅ HOÀN TẤT SETUP PREFERENCES!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi setup preferences: {e}")
        print("="*60)
    finally:
        # Đảm bảo luôn switch về default content
        try:
            driver.switch_to.default_content()
        except:
            pass


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