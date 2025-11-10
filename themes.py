from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element, click_save_button

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