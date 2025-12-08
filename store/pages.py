from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button

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