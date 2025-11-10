from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element, click_save_button

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