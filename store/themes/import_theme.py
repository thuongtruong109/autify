from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button, find_iframe_with_element
import os
import sys

# Determine base path for resources
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

def import_theme(driver: webdriver.Chrome, storeId: str):
    print("\n" + "="*60)
    print("🎨 IMPORT THEME...")
    print("="*60)

    try:
        # 1. Vào trang themes
        themes_url = f"https://admin.shopify.com/store/{storeId}/themes"
        print(f"Đang vào trang: {themes_url}")
        driver.get(themes_url)
        delay(3)

        # 2. Tìm iframe chứa element "Import theme" và thực hiện các thao tác
        print("🔍 Tìm iframe chứa 'Import theme'...")

        # Tìm tất cả iframes trong trang
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        import_theme_iframe = None

        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                print(f"   Kiểm tra iframe {i+1}/{len(iframes)}...")

                # Tìm element "Import theme" trong iframe
                try:
                    import_button = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            "//span[@class='Polaris-Text--root Polaris-Text--bodySm Polaris-Text--medium'][normalize-space()='Import theme']"
                        ))
                    )
                    print(f"✅ Tìm thấy 'Import theme' trong iframe {i+1}!")
                    import_theme_iframe = iframe
                    break
                except:
                    driver.switch_to.default_content()
                    continue

            except Exception as e:
                print(f"   Lỗi khi kiểm tra iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue

        if not import_theme_iframe:
            raise Exception("Không tìm thấy iframe chứa 'Import theme'")

        # Đã switch vào iframe chứa Import theme
        print("🔍 Tìm và click 'Import theme'...")
        wait = WebDriverWait(driver, 10)
        import_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//span[@class='Polaris-Text--root Polaris-Text--bodySm Polaris-Text--medium'][normalize-space()='Import theme']"
            ))
        )
        highlight_element(driver, import_button)
        print("✅ Tìm thấy 'Import theme'. Click...")
        driver.execute_script("arguments[0].click();", import_button)
        delay(2)
        print("✅ Đã click 'Import theme'.")

        # Chờ menu dropdown mở ra và tìm "Upload zip file" trong cùng iframe
        print("🔍 Chờ menu dropdown và tìm 'Upload zip file'...")
        upload_zip = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//span[@class='Polaris-Text--root Polaris-Text--bodyMd Polaris-Text--regular'][normalize-space()='Upload zip file']"
            ))
        )
        highlight_element(driver, upload_zip)
        print("✅ Tìm thấy 'Upload zip file' trong menu. Click...")
        driver.execute_script("arguments[0].click();", upload_zip)
        delay(2)
        print("✅ Đã click 'Upload zip file'.")

        # Switch về default content để tìm modal
        driver.switch_to.default_content()

        # Chờ modal mở ra
        print("🔍 Chờ modal upload mở ra...")
        modal = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]"
            ))
        )
        print("✅ Modal upload đã mở.")

        # Tìm iframe trong modal
        modal_iframe = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]//iframe"
            ))
        )
        print("✅ Tìm thấy iframe trong modal.")

        # Switch vào iframe của modal
        driver.switch_to.frame(modal_iframe)

        # Tìm và click "Add file" trong iframe của modal
        print("🔍 Tìm và click 'Add file' trong modal...")
        add_file_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//span[@class='Polaris-Text--root Polaris-Text--bodySm Polaris-Text--medium'][normalize-space()='Add file']"
            ))
        )
        highlight_element(driver, add_file_button)
        print("✅ Tìm thấy 'Add file'. Click...")
        driver.execute_script("arguments[0].click();", add_file_button)
        delay(2)
        print("✅ Đã click 'Add file'.")

        # Tìm file input và upload Theme6.zip
        print("🔍 Tìm file input để upload Theme6.zip...")
        file_input = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input[@type='file']"
            ))
        )
        theme_file_path = os.path.join(base_path, "Theme6.zip")
        print(f"📁 Đường dẫn file: {theme_file_path}")
        file_input.send_keys(theme_file_path)
        print("✅ Đã chọn file Theme6.zip để upload.")

        # Chờ upload hoàn thành và button "Upload file" được enable
        print("🔍 Chờ upload hoàn thành và button 'Upload file' được enable...")
        upload_file_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class, 'Polaris-Button--variantPrimary') and @aria-disabled='false']//span[normalize-space()='Upload file']"
            ))
        )
        highlight_element(driver, upload_file_button)
        print("✅ Upload hoàn thành, button 'Upload file' đã enable. Click...")
        driver.execute_script("arguments[0].click();", upload_file_button)
        delay(2)
        print("✅ Đã click 'Upload file'.")

        # Switch về default content
        driver.switch_to.default_content()

        # Chờ modal đóng lại
        print("🔍 Chờ modal upload đóng lại...")
        wait.until(
            EC.invisibility_of_element_located((
                By.XPATH,
                "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]"
            ))
        )
        print("✅ Modal đã đóng.")

        # Tìm iframe chứa button "Publish"
        print("🔍 Tìm iframe chứa button 'Publish'...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        publish_iframe = None

        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                print(f"   Kiểm tra iframe {i+1}/{len(iframes)}...")

                # Tìm button "Publish" trong iframe
                try:
                    publish_button = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            "//button[contains(@class, 'Polaris-Button--variantSecondary')]//span[normalize-space()='Publish']"
                        ))
                    )
                    print(f"✅ Tìm thấy 'Publish' trong iframe {i+1}!")
                    publish_iframe = iframe
                    break
                except:
                    driver.switch_to.default_content()
                    continue

            except Exception as e:
                print(f"   Lỗi khi kiểm tra iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue

        if not publish_iframe:
            raise Exception("Không tìm thấy iframe chứa 'Publish'")

        # Đã switch vào iframe chứa Publish
        print("🔍 Tìm button 'Publish'...")
        # Tìm button element (không phải span)
        publish_button = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[contains(@class, 'Polaris-Button--variantSecondary') and .//span[normalize-space()='Publish']]"
            ))
        )

        # Chờ button enable - kiểm tra không còn class disabled và aria-disabled không phải "true"
        print("🔍 Đang chờ button 'Publish' enable (chờ tới khi nào nó không còn disabled)...")
        WebDriverWait(driver, 300).until(  # Chờ tối đa 5 phút
            lambda d: (
                publish_button.get_attribute("aria-disabled") != "true" and
                "Polaris-Button--disabled" not in publish_button.get_attribute("class")
            )
        )

        print("✅ Button 'Publish' đã enable!")
        highlight_element(driver, publish_button)
        print("🔍 Đang click button 'Publish'...")
        driver.execute_script("arguments[0].click();", publish_button)
        delay(2)
        print("✅ Đã click 'Publish' thành công!")

        # Chờ modal Publish mở ra sau khi click Publish
        print("🔍 Chờ modal Publish mở ra...")
        try:
            modal_publish = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(@class, 'Polaris-Modal') and contains(@class, 'Polaris-Modal--sizeSmall')]"
                ))
            )
            print("✅ Modal Publish đã mở.")
        except:
            print("⚠️ Không tìm thấy modal Publish, thử tìm iframe trực tiếp...")

        # Tìm iframe trong modal Publish
        print("🔍 Tìm iframe trong modal Publish...")
        try:
            publish_modal_iframe = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//iframe[contains(@src, 'publish') or contains(@title, 'Publish')]"
                ))
            )
            print("✅ Tìm thấy iframe Publish.")
        except:
            # Nếu không tìm thấy iframe cụ thể, tìm tất cả iframe
            driver.switch_to.default_content()
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            publish_modal_iframe = None

            for i, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    print(f"   Kiểm tra iframe {i+1}/{len(iframes)}...")

                    # Tìm button Publish trong iframe
                    try:
                        confirm_publish_button = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((
                                By.XPATH,
                                "//button[contains(@class, 'Polaris-Button--variantPrimary') and .//span[normalize-space()='Publish']]"
                            ))
                        )
                        print(f"✅ Tìm thấy button 'Publish' trong iframe {i+1}!")
                        publish_modal_iframe = iframe
                        break
                    except:
                        driver.switch_to.default_content()
                        continue

                except Exception as e:
                    print(f"   Lỗi khi kiểm tra iframe {i+1}: {e}")
                    driver.switch_to.default_content()
                    continue

            if not publish_modal_iframe:
                raise Exception("Không tìm thấy iframe chứa button 'Publish' trong modal")

        # Đã switch vào iframe chứa button Publish trong modal
        print("🔍 Tìm button 'Publish' trong modal...")
        confirm_publish_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[@class='Polaris-Button Polaris-Button--pressable Polaris-Button--variantPrimary Polaris-Button--sizeMedium Polaris-Button--textAlignCenter' and @aria-disabled='false' and .//span[normalize-space()='Publish']]"
            ))
        )

        print("✅ Tìm thấy button 'Publish' trong modal!")
        highlight_element(driver, confirm_publish_button)
        print("🔍 Đang click button 'Publish' trong modal...")
        driver.execute_script("arguments[0].click();", confirm_publish_button)
        delay(2)
        print("✅ Đã click 'Publish' trong modal thành công!")

        # Switch về default content
        driver.switch_to.default_content()

        print("\n✅ HOÀN TẤT IMPORT THEME!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi import theme: {e}")
        print("="*60)