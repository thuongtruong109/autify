from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button, find_iframe_with_element
import os
import sys

def get_theme_path():
    if hasattr(sys, '_MEIPASS'):
        base_dir = os.path.join(sys._MEIPASS, "themes")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_dir, "Theme6.zip")

theme_file_path = get_theme_path()

def import_theme(driver: webdriver.Chrome, storeId: str):
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
        print("🔍 Tìm và click 'Import theme' với RETRY LOGIC...")
        wait = WebDriverWait(driver, 10)

        # STRATEGY 1: Multiple selectors
        import_selectors = [
            "//span[@class='Polaris-Text--root Polaris-Text--bodySm Polaris-Text--medium'][normalize-space()='Import theme']",
            "//span[normalize-space()='Import theme']",
            "//button[.//span[normalize-space()='Import theme']]"
        ]

        import_button = None
        for selector in import_selectors:
            try:
                import_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                print(f"   ✅ Tìm thấy 'Import theme' với selector: {selector[:60]}...")
                break
            except:
                continue

        if not import_button:
            raise Exception("Không tìm thấy button 'Import theme'")

        # STRATEGY 2: Scroll và highlight
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", import_button)
        delay(1)
        highlight_element(driver, import_button)

        # STRATEGY 3: Retry click
        print("🔍 Đang click 'Import theme'...")
        click_success = False

        for attempt in range(3):
            try:
                if attempt > 0:
                    delay(1)

                driver.execute_script("arguments[0].click();", import_button)
                delay(2)

                # Verify: Check dropdown menu xuất hiện
                try:
                    driver.find_element(By.XPATH, "//span[normalize-space()='Upload zip file']")
                    print("   ✅ Click thành công! (dropdown đã mở)")
                    click_success = True
                    break
                except:
                    print("   ⚠️ Dropdown chưa mở, thử lại...")
                    continue

            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                continue

        if not click_success:
            raise Exception("Không thể click 'Import theme' sau 3 lần thử")

        print("✅ Đã click 'Import theme' thành công!")

        # Chờ menu dropdown mở ra và tìm "Upload zip file" với RETRY LOGIC
        print("🔍 Chờ menu dropdown và tìm 'Upload zip file'...")

        # STRATEGY 1: Multiple selectors
        upload_zip_selectors = [
            "//span[@class='Polaris-Text--root Polaris-Text--bodyMd Polaris-Text--regular'][normalize-space()='Upload zip file']",
            "//span[normalize-space()='Upload zip file']",
            "//button[.//span[normalize-space()='Upload zip file']]",
            "//a[.//span[normalize-space()='Upload zip file']]"
        ]

        upload_zip = None
        for selector in upload_zip_selectors:
            try:
                upload_zip = wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                print(f"   ✅ Tìm thấy 'Upload zip file' với selector: {selector[:60]}...")
                break
            except:
                continue

        if not upload_zip:
            raise Exception("Không tìm thấy 'Upload zip file' trong menu")

        # STRATEGY 2: Scroll và highlight
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", upload_zip)
        delay(1)
        highlight_element(driver, upload_zip)

        # STRATEGY 3: Retry click
        print("🔍 Đang click 'Upload zip file'...")
        click_success = False

        for attempt in range(3):
            try:
                if attempt > 0:
                    delay(1)

                driver.execute_script("arguments[0].click();", upload_zip)
                delay(2)

                # Verify: Check modal xuất hiện
                driver.switch_to.default_content()
                try:
                    driver.find_element(By.XPATH, "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]")
                    print("   ✅ Click thành công! (modal đã mở)")
                    click_success = True
                    break
                except:
                    print("   ⚠️ Modal chưa mở, thử lại...")
                    # Switch lại vào iframe
                    driver.switch_to.frame(import_theme_iframe)
                    continue

            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                continue

        if not click_success:
            raise Exception("Không thể click 'Upload zip file' sau 3 lần thử")

        print("✅ Đã click 'Upload zip file' thành công!")

        # Đã switch về default content trong phần trước
        # Chờ modal mở ra (đã verify trong click trước)
        print("✅ Modal upload đã mở.")

        # Tìm iframe trong modal với RETRY LOGIC
        print("🔍 Tìm iframe trong modal...")
        modal_iframe = None

        for iframe_attempt in range(5):  # Retry 5 lần
            try:
                modal_iframe = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]//iframe"
                    ))
                )

                # Kiểm tra iframe có visible không
                if modal_iframe.is_displayed():
                    print(f"✅ Tìm thấy iframe trong modal (attempt {iframe_attempt + 1}).")
                    break
                else:
                    print(f"   ⚠️ Iframe chưa visible, đợi thêm... (attempt {iframe_attempt + 1})")
                    delay(1)
                    continue

            except Exception as e:
                print(f"   ⚠️ Chưa tìm thấy iframe (attempt {iframe_attempt + 1}): {e}")
                if iframe_attempt < 4:
                    delay(1)
                    continue
                else:
                    raise Exception("Không tìm thấy iframe trong modal sau 5 lần thử")

        if not modal_iframe:
            raise Exception("Không tìm thấy iframe trong modal")

        # Switch vào iframe của modal với RETRY
        print("🔍 Đang switch vào iframe của modal...")
        switch_success = False

        for switch_attempt in range(3):  # Retry switch 3 lần
            try:
                driver.switch_to.frame(modal_iframe)
                print(f"✅ Đã switch vào iframe (attempt {switch_attempt + 1}).")

                # QUAN TRỌNG: Đợi iframe load xong nội dung bên trong
                delay(2)

                # Verify: Thử tìm một element nào đó trong iframe để đảm bảo đã load
                try:
                    driver.find_element(By.XPATH, "//body")
                    print("✅ Iframe đã load xong nội dung.")
                    switch_success = True
                    break
                except:
                    print(f"   ⚠️ Iframe chưa load xong, thử lại... (attempt {switch_attempt + 1})")
                    driver.switch_to.default_content()
                    delay(1)
                    continue

            except Exception as e:
                print(f"   ⚠️ Lỗi switch vào iframe (attempt {switch_attempt + 1}): {e}")
                driver.switch_to.default_content()
                if switch_attempt < 2:
                    delay(1)
                    continue
                else:
                    raise Exception("Không thể switch vào iframe sau 3 lần thử")

        if not switch_success:
            raise Exception("Không thể switch vào iframe modal")

        # Tìm và click "Add file" trong iframe của modal với RETRY LOGIC
        print("🔍 Tìm và click 'Add file' trong modal...")

        # STRATEGY 1: Tìm button bằng nhiều cách khác nhau với TIMEOUT DÀI
        add_file_selectors = [
            "//span[@class='Polaris-Text--root Polaris-Text--bodySm Polaris-Text--medium'][normalize-space()='Add file']",
            "//span[normalize-space()='Add file']",
            "//button[.//span[normalize-space()='Add file']]",
            "//a[.//span[normalize-space()='Add file']]"
        ]

        add_file_button = None
        wait_long = WebDriverWait(driver, 20)  # Tăng timeout lên 20s vì iframe có thể load chậm

        for selector_idx, selector in enumerate(add_file_selectors):
            try:
                print(f"   🔍 Thử selector {selector_idx + 1}/{len(add_file_selectors)}: {selector[:60]}...")
                add_file_button = wait_long.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )

                # Verify element visible
                if add_file_button.is_displayed():
                    print(f"   ✅ Tìm thấy 'Add file' với selector {selector_idx + 1}!")
                    break
                else:
                    print(f"   ⚠️ Tìm thấy nhưng không visible, thử selector khác...")
                    add_file_button = None
                    continue

            except Exception as e:
                print(f"   ⚠️ Selector {selector_idx + 1} failed: {e}")
                continue

        if not add_file_button:
            # Debug: In ra HTML của iframe để xem có gì
            print("❌ Không tìm thấy 'Add file' button. Debug info:")
            try:
                html_content = driver.execute_script("return document.body.innerHTML;")
                print(f"   HTML length: {len(html_content)} chars")
                # Tìm xem có chữ "Add" không
                if "Add" in html_content:
                    print("   ✅ Có chữ 'Add' trong HTML")
                else:
                    print("   ❌ KHÔNG có chữ 'Add' trong HTML - iframe có thể chưa load!")
            except Exception as debug_e:
                print(f"   ⚠️ Không thể debug: {debug_e}")

            raise Exception("Không tìm thấy button 'Add file' với bất kỳ selector nào")

        # STRATEGY 2: Scroll và chờ element thực sự sẵn sàng
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", add_file_button)
        delay(1)

        # Highlight để debug
        highlight_element(driver, add_file_button)

        # STRATEGY 3: Retry click với nhiều methods
        print("🔍 Đang thử click 'Add file' với retry logic...")
        click_success = False

        for attempt in range(5):  # Retry 5 lần
            try:
                print(f"   Attempt {attempt + 1}/5...")

                # Wait thêm một chút giữa các lần thử
                if attempt > 0:
                    delay(1)

                # Method 1: JavaScript click (thường reliable nhất)
                try:
                    driver.execute_script("arguments[0].click();", add_file_button)
                    delay(1)

                    # Verify click thành công bằng cách check file input có xuất hiện không
                    try:
                        driver.find_element(By.XPATH, "//input[@type='file']")
                        print("   ✅ Click thành công! (file input đã xuất hiện)")
                        click_success = True
                        break
                    except:
                        # Chưa thấy file input, thử lại
                        print("   ⚠️ Chưa thấy file input, thử lại...")
                        continue

                except Exception as e:
                    print(f"   ⚠️ JavaScript click failed: {e}")

                    # Method 2: Selenium native click
                    try:
                        # Tìm lại button để tránh stale element
                        add_file_button = driver.find_element(By.XPATH, add_file_selectors[0])
                        add_file_button.click()
                        delay(1)

                        # Verify
                        try:
                            driver.find_element(By.XPATH, "//input[@type='file']")
                            print("   ✅ Click thành công! (selenium click)")
                            click_success = True
                            break
                        except:
                            print("   ⚠️ Chưa thấy file input, thử lại...")
                            continue

                    except Exception as e2:
                        print(f"   ⚠️ Selenium click failed: {e2}")
                        continue

            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                continue

        if not click_success:
            raise Exception("Không thể click 'Add file' sau 5 lần thử")

        print("✅ Đã click 'Add file' thành công!")
        delay(1)

        # Tìm file input và upload Theme6.zip
        print("🔍 Tìm file input để upload Theme6.zip...")
        file_input = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input[@type='file']"
            ))
        )
        # theme_file_path = os.path.join(base_path, "Theme6.zip")
        print(f"📁 Đường dẫn file: {theme_file_path}")
        file_input.send_keys(theme_file_path)
        print("✅ Đã chọn file Theme6.zip để upload.")

        # Chờ upload hoàn thành và button "Upload file" được enable với RETRY LOGIC
        print("🔍 Chờ upload hoàn thành và button 'Upload file' được enable...")

        # STRATEGY 1: Tìm button bằng nhiều selectors
        upload_file_selectors = [
            "//button[contains(@class, 'Polaris-Button--variantPrimary') and @aria-disabled='false']//span[normalize-space()='Upload file']",
            "//button[@aria-disabled='false']//span[normalize-space()='Upload file']",
            "//span[normalize-space()='Upload file']",
            "//button[.//span[normalize-space()='Upload file']]"
        ]

        upload_file_button = None
        for selector in upload_file_selectors:
            try:
                # Chờ button xuất hiện VÀ enabled
                upload_file_button = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )

                # Kiểm tra thêm aria-disabled
                parent_button = upload_file_button if upload_file_button.tag_name == 'button' else upload_file_button.find_element(By.XPATH, "./ancestor::button")
                if parent_button.get_attribute("aria-disabled") == "false":
                    print(f"   ✅ Tìm thấy 'Upload file' enabled với selector: {selector[:60]}...")
                    upload_file_button = parent_button
                    break
            except:
                continue

        if not upload_file_button:
            raise Exception("Không tìm thấy button 'Upload file' enabled")

        # STRATEGY 2: Scroll và highlight
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", upload_file_button)
        delay(1)
        highlight_element(driver, upload_file_button)

        # STRATEGY 3: Retry click với verification
        print("🔍 Đang thử click 'Upload file' với retry logic...")
        click_success = False

        for attempt in range(5):  # Retry 5 lần
            try:
                print(f"   Attempt {attempt + 1}/5...")

                if attempt > 0:
                    delay(1)
                    # Tìm lại button để tránh stale element
                    try:
                        upload_file_button = driver.find_element(By.XPATH, upload_file_selectors[0])
                    except:
                        upload_file_button = driver.find_element(By.XPATH, upload_file_selectors[1])

                # Method 1: JavaScript click
                try:
                    driver.execute_script("arguments[0].click();", upload_file_button)
                    delay(2)

                    # Verify: Check modal có đóng không (sau khi upload)
                    try:
                        # Nếu modal vẫn còn visible sau 2s → click chưa work
                        driver.switch_to.default_content()
                        modal_still_visible = driver.find_elements(By.XPATH, "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]")

                        if len(modal_still_visible) == 0:
                            print("   ✅ Click thành công! (modal đã đóng)")
                            click_success = True
                            break
                        else:
                            # Modal vẫn còn, switch lại vào iframe và thử lại
                            print("   ⚠️ Modal vẫn còn, thử lại...")
                            driver.switch_to.frame(modal_iframe)
                            continue
                    except:
                        # Lỗi khi check modal → có thể đã đóng
                        print("   ✅ Click có vẻ thành công!")
                        click_success = True
                        break

                except Exception as e:
                    print(f"   ⚠️ JavaScript click failed: {e}")

                    # Method 2: Selenium native click
                    try:
                        upload_file_button.click()
                        delay(2)

                        # Verify
                        driver.switch_to.default_content()
                        modal_still_visible = driver.find_elements(By.XPATH, "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]")

                        if len(modal_still_visible) == 0:
                            print("   ✅ Click thành công! (selenium click)")
                            click_success = True
                            break
                        else:
                            print("   ⚠️ Modal vẫn còn, thử lại...")
                            driver.switch_to.frame(modal_iframe)
                            continue

                    except Exception as e2:
                        print(f"   ⚠️ Selenium click failed: {e2}")
                        continue

            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                continue

        if not click_success:
            raise Exception("Không thể click 'Upload file' sau 5 lần thử")

        print("✅ Đã click 'Upload file' thành công!")

        # Đã switch về default content trong verify click rồi
        # Chờ modal đóng lại với retry
        print("🔍 Chờ modal upload đóng lại...")
        for wait_attempt in range(30):  # Chờ tối đa 30s
            try:
                modal_elements = driver.find_elements(By.XPATH, "//div[contains(@class, '_Container_1w897_1') and contains(@class, '_visible_1w897_15')]")
                if len(modal_elements) == 0:
                    print("✅ Modal đã đóng.")
                    break
                else:
                    print(f"   ⏳ Modal vẫn còn, đợi... ({wait_attempt + 1}/30)")
                    delay(1)
            except:
                print("✅ Modal đã đóng.")
                break
        else:
            print("⚠️ Modal vẫn chưa đóng sau 30s, nhưng tiếp tục...")

        delay(2)

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

        # STRATEGY: Retry click với verification
        print("🔍 Đang click button 'Publish' với retry logic...")
        click_success = False

        for attempt in range(3):
            try:
                if attempt > 0:
                    delay(1)
                    # Tìm lại button
                    publish_button = driver.find_element(By.XPATH, "//button[contains(@class, 'Polaris-Button--variantSecondary') and .//span[normalize-space()='Publish']]")

                highlight_element(driver, publish_button)
                driver.execute_script("arguments[0].click();", publish_button)
                delay(2)

                # Verify: Check modal Publish xuất hiện
                driver.switch_to.default_content()
                try:
                    driver.find_element(By.XPATH, "//div[contains(@class, 'Polaris-Modal')]")
                    print("   ✅ Click thành công! (modal Publish đã mở)")
                    click_success = True
                    break
                except:
                    print("   ⚠️ Modal Publish chưa mở, thử lại...")
                    # Switch lại vào iframe
                    driver.switch_to.frame(publish_iframe)
                    continue

            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                continue

        if not click_success:
            raise Exception("Không thể click 'Publish' sau 3 lần thử")

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
        print("🔍 Tìm button 'Publish' trong modal với RETRY LOGIC...")

        # STRATEGY 1: Multiple selectors
        confirm_publish_selectors = [
            "//button[@class='Polaris-Button Polaris-Button--pressable Polaris-Button--variantPrimary Polaris-Button--sizeMedium Polaris-Button--textAlignCenter' and @aria-disabled='false' and .//span[normalize-space()='Publish']]",
            "//button[contains(@class, 'Polaris-Button--variantPrimary') and @aria-disabled='false' and .//span[normalize-space()='Publish']]",
            "//button[@aria-disabled='false']//span[normalize-space()='Publish']"
        ]

        confirm_publish_button = None
        for selector in confirm_publish_selectors:
            try:
                confirm_publish_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                print(f"   ✅ Tìm thấy confirm 'Publish' với selector: {selector[:70]}...")
                break
            except:
                continue

        if not confirm_publish_button:
            raise Exception("Không tìm thấy button 'Publish' trong modal")

        # STRATEGY 2: Scroll và highlight
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", confirm_publish_button)
        delay(1)
        highlight_element(driver, confirm_publish_button)

        # STRATEGY 3: Retry click
        print("🔍 Đang click button 'Publish' trong modal...")
        click_success = False

        for attempt in range(3):
            try:
                if attempt > 0:
                    delay(1)
                    # Tìm lại button
                    try:
                        confirm_publish_button = driver.find_element(By.XPATH, confirm_publish_selectors[0])
                    except:
                        confirm_publish_button = driver.find_element(By.XPATH, confirm_publish_selectors[1])

                driver.execute_script("arguments[0].click();", confirm_publish_button)
                delay(3)

                # Verify: Check modal đã đóng
                driver.switch_to.default_content()
                try:
                    # Nếu modal vẫn còn → click chưa work
                    modal_still_there = driver.find_elements(By.XPATH, "//div[contains(@class, 'Polaris-Modal')]")
                    if len(modal_still_there) == 0:
                        print("   ✅ Click thành công! (modal đã đóng)")
                        click_success = True
                        break
                    else:
                        print("   ⚠️ Modal vẫn còn, thử lại...")
                        # Switch lại vào iframe
                        if publish_modal_iframe:
                            driver.switch_to.frame(publish_modal_iframe)
                        continue
                except:
                    print("   ✅ Click có vẻ thành công!")
                    click_success = True
                    break

            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                continue

        if not click_success:
            raise Exception("Không thể click 'Publish' trong modal sau 3 lần thử")

        print("✅ Đã click 'Publish' trong modal thành công!")

        # Switch về default content
        driver.switch_to.default_content()

        print("\n✅ HOÀN TẤT IMPORT THEME!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi import theme: {e}")
        print("="*60)