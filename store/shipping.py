from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button

def setup_shipping_zones(driver: webdriver.Chrome, storeId: str, should_stop_callback=None):
    print("\n" + "="*60)
    print("🚚 SETUP SHIPPING ZONES...")
    print("="*60)

    try:
        shipping_url = f"https://admin.shopify.com/store/{storeId}/settings/shipping"
        print(f"Đang vào trang: {shipping_url}")
        driver.get(shipping_url)
        delay(3)

        # Kiểm tra verification message và chờ đến khi nó biến mất
        max_verification_checks = 10  # Tối đa 10 lần check (20 giây)
        verification_message_found = False

        for check_attempt in range(max_verification_checks):
            # Check stop flag
            if should_stop_callback and should_stop_callback():
                print("\n⏹️ DỪNG TASK - User đã nhấn Stop button")
                return
            try:
                verification_element = driver.find_element(
                    By.XPATH,
                    "//*[contains(text(), 'Your connection needs to be verified before you can proceed')]"
                )

                if check_attempt == 0:
                    print("⚠️ Phát hiện verification message. Đang chờ xác minh...")
                    verification_message_found = True

                print(f"   [Check {check_attempt + 1}/{max_verification_checks}] Verification message vẫn còn. Đợi 2s...")
                delay(2)

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
        try:
            general_rates_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'General shipping rates')]"))
            )
            highlight_element(driver, general_rates_element)
            driver.execute_script("arguments[0].click();", general_rates_element)
            delay(2)

            # 2. Tìm button thứ 2 với aria-label="More actions" và click
            try:
                more_actions_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[2]"))
                )
                highlight_element(driver, more_actions_btn)
                driver.execute_script("arguments[0].click();", more_actions_btn)
                delay(2)

                # 2a. Chờ menu 'Polaris-Popover__Content' xuất hiện và tìm 'Edit zone'
                try:
                    menu = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                    )

                    # 2b. Tìm element có chữ "Edit rate" trong menu
                    edit_zone_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Edit rate')]")
                    highlight_element(driver, edit_zone_element)
                    driver.execute_script("arguments[0].click();", edit_zone_element)
                    delay(1)

                    # 2c. Chờ modal xuất hiện sau khi click "Edit rate"
                    try:
                        modal = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                        )
                        delay(1)

                        # 2d. Tìm select element và chọn option đầu tiên
                        try:
                            select_element = modal.find_element(By.TAG_NAME, "select")
                            highlight_element(driver, select_element)

                            # Lấy tất cả options và chọn option đầu tiên
                            options = select_element.find_elements(By.TAG_NAME, "option")
                            if options:
                                print(f"✅ Tìm thấy {len(options)} options. Chọn option đầu tiên...")
                                driver.execute_script("arguments[0].selectedIndex = 0; arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_element)
                                delay(0.5)
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy select element: {e}")

                        # 2e. Tìm input name="amount" và sửa thành "9.99"
                        try:
                            amount_input = modal.find_element(By.CSS_SELECTOR, "input[name='amount']")
                            highlight_element(driver, amount_input)

                            # Click vào input để focus
                            amount_input.click()
                            delay(0.3)

                            # Cách 1: Dùng Ctrl+A để select all, sau đó gõ đè
                            amount_input.send_keys(Keys.CONTROL + "a")
                            delay(0.3)
                            amount_input.send_keys(Keys.DELETE)
                            delay(0.3)

                            # Cách 2: Clear bằng JavaScript để chắc chắn
                            driver.execute_script("arguments[0].value = '';", amount_input)
                            delay(0.3)

                            # Triple click để select all (phòng trường hợp)
                            driver.execute_script("arguments[0].select();", amount_input)
                            delay(0.3)

                            # Nhập giá trị mới
                            amount_input.send_keys("9.99")
                            delay(1)
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy input name='amount': {e}")

                        # 2f. Tìm và click element "Remove conditional pricing"
                        try:
                            remove_conditional = modal.find_element(By.XPATH, ".//*[contains(text(), 'Remove conditional pricing')]")
                            highlight_element(driver, remove_conditional)
                            driver.execute_script("arguments[0].click();", remove_conditional)
                            delay(1)
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy 'Remove conditional pricing': {e}")

                        # 2j. Tìm và click button "Done"
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
                                driver.execute_script("arguments[0].click();", done_button)
                                delay(2)

                                # Wait modal closed
                                try:
                                    WebDriverWait(driver, 10).until(
                                        EC.invisibility_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                                    )
                                    delay(1)
                                except Exception as e:
                                    print(f"⚠️ Không thể xác nhận modal đã đóng: {e}")
                                    delay(1)
                            else:
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

            # 3. Find and click to 3rd button has aria-label="More actions"
            try:
                more_actions_btn_3 = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[3]"))
                )
                highlight_element(driver, more_actions_btn_3)
                driver.execute_script("arguments[0].click();", more_actions_btn_3)
                delay(1)

                # 3a. Chờ menu 'Polaris-Popover__Content' xuất hiện và tìm 'Edit zone'
                try:
                    menu = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                    )

                    # 3b. Tìm element có chữ "Edit rate" trong menu
                    edit_zone_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Edit rate')]")
                    highlight_element(driver, edit_zone_element)
                    driver.execute_script("arguments[0].click();", edit_zone_element)
                    delay(1)

                    # 3c. Chờ modal xuất hiện sau khi click "Edit rate"
                    try:
                        modal = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                        )
                        delay(1)

                        # 3d. Tìm select element và chọn option thứ 2
                        try:
                            select_element = modal.find_element(By.TAG_NAME, "select")
                            highlight_element(driver, select_element)

                            # Lấy tất cả options và chọn option thứ 2
                            options = select_element.find_elements(By.TAG_NAME, "option")
                            if len(options) >= 2:
                                driver.execute_script("arguments[0].selectedIndex = 1; arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_element)
                                delay(1)
                            else:
                                print(f"⚠️ Chỉ có {len(options)} option(s), không đủ để chọn option thứ 2.")
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy select element: {e}")

                        # 3e. Tìm input name="amount" và sửa thành "0.00"
                        try:
                            amount_input = modal.find_element(By.CSS_SELECTOR, "input[name='amount']")
                            highlight_element(driver, amount_input)

                            # Click vào input để focus
                            amount_input.click()
                            delay(0.3)

                            # Cách 1: Dùng Ctrl+A để select all, sau đó gõ đè
                            amount_input.send_keys(Keys.CONTROL + "a")
                            delay(0.3)
                            amount_input.send_keys(Keys.DELETE)
                            delay(0.3)

                            # Cách 2: Clear bằng JavaScript để chắc chắn
                            driver.execute_script("arguments[0].value = '';", amount_input)
                            delay(0.3)

                            # Triple click để select all (phòng trường hợp)
                            driver.execute_script("arguments[0].select();", amount_input)
                            delay(0.3)

                            # Nhập giá trị mới
                            amount_input.send_keys("0.00")
                            delay(1)
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy input name='amount': {e}")

                        # 3f. Tìm và click element "Remove conditional pricing"
                        try:
                            remove_conditional = modal.find_element(By.XPATH, ".//*[contains(text(), 'Remove conditional pricing')]")
                            highlight_element(driver, remove_conditional)
                            driver.execute_script("arguments[0].click();", remove_conditional)
                            delay(1)
                        except Exception as e:
                            print(f"⚠️ Không tìm thấy 'Remove conditional pricing': {e}")

                        # 3j. Tìm và click button "Done"
                        done_button = None
                        try:
                            # Cách 1: Tìm button có text "Done" trực tiếp
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[contains(text(), 'Done')]")
                            except:
                                pass

                            # Cách 2: Tìm button có descendant chứa text "Done"
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[.//*[contains(text(), 'Done')]]")
                                except:
                                    pass

                            # Cách 3: Tìm button có normalize-space text = "Done"
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[normalize-space()='Done' or .//*[normalize-space()='Done']]")
                                except:
                                    pass

                            # Cách 4: Tìm button có text chứa "Done" (case-insensitive)
                            if not done_button:
                                try:
                                    done_button = modal.find_element(By.XPATH, ".//button[contains(translate(., 'DONE', 'done'), 'done') or .//*[contains(translate(., 'DONE', 'done'), 'done')]]")
                                except:
                                    pass

                            # Cách 5: Tìm tất cả buttons trong modal và kiểm tra text
                            if not done_button:
                                try:
                                    all_buttons = modal.find_elements(By.XPATH, ".//button")
                                    for btn in all_buttons:
                                        btn_text = btn.text.strip().lower()
                                        if 'done' in btn_text:
                                            done_button = btn
                                            break
                                except Exception as e:
                                    print(f"⚠️ Lỗi khi quét buttons: {e}")

                            # Click button nếu tìm thấy
                            if done_button:
                                highlight_element(driver, done_button)
                                driver.execute_script("arguments[0].click();", done_button)
                                delay(1)
                            else:
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

            # 4. Find and click to 4th button has aria-label="More actions" (after remove will shift index)
            for val in [4, 4, 4, 5, 5]:
                tmp = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"(//button[@aria-label='More actions'])[{val}]"))
                )
                highlight_element(driver, tmp)
                driver.execute_script("arguments[0].click();", tmp)
                delay(1)

                # 4a. Wait menu appears and find 'Delete'
                try:
                    menu = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                    )

                    # 4b. Tìm element có chữ "Delete" trong menu
                    delete_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Delete')]")
                    highlight_element(driver, delete_element)
                    driver.execute_script("arguments[0].click();", delete_element)
                    delay(1)

                except Exception as e:
                    print(f"⚠️ Không tìm thấy menu hoặc 'Delete': {e}")

            # 5. Edit International shipping zones
            inter_ship = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "(//button[@aria-label='More actions'])[4]"))
            )
            highlight_element(driver, inter_ship)
            driver.execute_script("arguments[0].click();", inter_ship)
            delay(1)

            # 5a. Wait menu appears and find 'Edit zone'
            try:
                menu = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Popover__Content"))
                )

                delete_element = menu.find_element(By.XPATH, ".//*[contains(text(), 'Edit zone')]")
                highlight_element(driver, delete_element)
                driver.execute_script("arguments[0].click();", delete_element)
                delay(1)

            except Exception as e:
                print(f"⚠️ Không tìm thấy menu hoặc 'Edit zone': {e}")

            # 5b. Đợi modal mở ra và click vào tất cả các checkbox trong modal
            try:
                modal = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                )
                delay(1)

                # Tìm scroll container (ReactVirtualized__Grid__innerScrollContainer)
                try:
                    scroll_container = modal.find_element(By.CSS_SELECTOR, ".ReactVirtualized__Grid__innerScrollContainer")
                except:
                    scroll_container = modal
                    print("⚠️ Không tìm thấy scroll container, dùng modal làm container")

                # Tìm tất cả các checkbox hiện tại
                clicked_count = 0
                processed_ids = set()  # Track các checkbox đã xử lý

                # Tìm element có thể scroll trong modal - target ReactVirtualized__Grid
                scrollable_element = None
                try:
                    try:
                        scrollable_element = modal.find_element(By.CSS_SELECTOR, ".ReactVirtualized__Grid")
                        scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_element)
                    except:
                        try:
                            scrollable_element = modal.find_element(By.CSS_SELECTOR, ".ReactVirtualized__List")
                            scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_element)
                        except:
                            try:
                                scrollable_element = modal.find_element(By.CSS_SELECTOR, "[role='grid']")
                                scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_element)
                            except:
                                print("⚠️ Không tìm thấy ReactVirtualized container")

                except Exception as e:
                    print(f"⚠️ Lỗi khi tìm scrollable element: {e}")

                # Scroll và click tất cả checkbox
                scroll_attempts = 0
                max_scroll_attempts = 100  # Tăng số lần scroll
                no_new_items_count = 0  # Đếm số lần không tìm thấy item mới liên tiếp

                while scroll_attempts < max_scroll_attempts:
                    checkboxes = modal.find_elements(By.CSS_SELECTOR, "input.Polaris-Checkbox__Input[type='checkbox']")

                    new_checkboxes_found = False
                    for checkbox in checkboxes:
                        try:
                            checkbox_id = checkbox.get_attribute("id")
                            if not checkbox_id or checkbox_id in processed_ids:
                                continue

                            new_checkboxes_found = True
                            processed_ids.add(checkbox_id)

                            is_checked = checkbox.is_selected()

                            if not is_checked:
                                try:
                                    driver.execute_script("arguments[0].click();", checkbox)
                                    clicked_count += 1
                                    delay(0.1)
                                except Exception as e:
                                    # Nếu click checkbox thất bại, thử click label
                                    try:
                                        label = modal.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
                                        driver.execute_script("arguments[0].click();", label)
                                        clicked_count += 1
                                        delay(0.1)
                                    except:
                                        print(f"⚠️ Không thể click checkbox: {checkbox_id}")
                            else:
                                print(f"○ Checkbox đã checked: {checkbox_id}")

                        except Exception as e:
                            print(f"⚠️ Lỗi khi xử lý checkbox: {e}")

                    # Scroll xuống để load thêm items
                    if scrollable_element:
                        try:
                            current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
                            max_scroll = driver.execute_script("return arguments[0].scrollHeight - arguments[0].clientHeight;", scrollable_element)

                            driver.execute_script("arguments[0].scrollTop += 300;", scrollable_element)
                            delay(0.3)

                            new_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)

                            # Kiểm tra nếu đã scroll đến cuối
                            if new_scroll >= max_scroll or current_scroll == new_scroll:
                                no_new_items_count += 1
                                if no_new_items_count >= 3:  # Nếu 3 lần liên tiếp không scroll được
                                    break
                            else:
                                no_new_items_count = 0  # Reset counter nếu vẫn scroll được
                        except Exception as e:
                            print(f"⚠️ Lỗi khi scroll: {e}")
                            break
                    else:
                        print("⚠️ Không tìm thấy scrollable element")
                        break

                    scroll_attempts += 1
                delay(1)

            except Exception as e:
                print(f"⚠️ Không tìm thấy modal hoặc lỗi khi xử lý checkboxes: {e}")

            # 5c. Tìm và click button "Done"
            try:
                done_button = modal.find_element(By.XPATH, ".//button[.//*[contains(text(), 'Done')]]")
                if done_button:
                    highlight_element(driver, done_button)
                    driver.execute_script("arguments[0].click();", done_button)
                    delay(1)
                else:
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

            # 6a. Add international rate 1
            try:
                # Tìm tất cả các element "Add rate" và chọn element cuối cùng
                add_rate_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add rate')]"))
                )

                if add_rate_buttons:
                    # Lấy element cuối cùng
                    add_rate_button = add_rate_buttons[-1]
                    highlight_element(driver, add_rate_button)
                    driver.execute_script("arguments[0].click();", add_rate_button)
                    delay(1)
                else:
                    print("⚠️ Không tìm thấy element 'Add rate'")
                    raise Exception("No 'Add rate' button found")

                # Đợi modal mở ra
                try:
                    modal = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                    )
                    delay(1)

                    # Tìm input name="amount" với id="Rates-Cost-TextField"
                    try:
                        amount_input = modal.find_element(By.CSS_SELECTOR, "input[name='amount'][id='Rates-Cost-TextField']")
                        highlight_element(driver, amount_input)

                        # Click vào input để focus
                        amount_input.click()
                        delay(0.3)

                        # Clear value bằng nhiều cách để đảm bảo
                        # Cách 1: Select all và delete
                        amount_input.send_keys(Keys.CONTROL + "a")
                        delay(0.2)
                        amount_input.send_keys(Keys.DELETE)
                        delay(0.2)

                        # Cách 2: Clear bằng JavaScript
                        driver.execute_script("arguments[0].value = '';", amount_input)
                        delay(0.2)

                        # Cách 3: Select bằng JavaScript
                        driver.execute_script("arguments[0].select();", amount_input)
                        delay(0.2)

                        # Nhập giá trị mới 9.99
                        amount_input.send_keys("9.99")
                        delay(0.5)

                    except Exception as e:
                        print(f"⚠️ Không tìm thấy input name='amount': {e}")

                    # Tìm và click button "Done"
                    try:
                        done_button = None

                        # Thử nhiều cách tìm button "Done"
                        try:
                            done_button = modal.find_element(By.XPATH, ".//button[contains(text(), 'Done')]")
                        except:
                            pass

                        if not done_button:
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[.//*[contains(text(), 'Done')]]")
                            except:
                                pass

                        if not done_button:
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[normalize-space()='Done' or .//*[normalize-space()='Done']]")
                            except:
                                pass

                        if not done_button:
                            # Tìm tất cả buttons và kiểm tra text
                            all_buttons = modal.find_elements(By.TAG_NAME, "button")
                            for btn in all_buttons:
                                btn_text = btn.text.strip().lower()
                                if 'done' in btn_text:
                                    done_button = btn
                                    break

                        if done_button:
                            highlight_element(driver, done_button)
                            driver.execute_script("arguments[0].click();", done_button)
                            delay(0.5)

                            # Đợi modal đóng
                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                                )
                                print("✅ Modal đã đóng")
                                delay(1)
                            except Exception as e:
                                print(f"⚠️ Không thể xác nhận modal đã đóng: {e}")
                                delay(1)
                        else:
                            print("⚠️ Không tìm thấy button 'Done'")

                    except Exception as e:
                        print(f"⚠️ Lỗi khi tìm button 'Done': {e}")

                except Exception as e:
                    print(f"⚠️ Không tìm thấy modal: {e}")

            except Exception as e:
                print(f"⚠️ Không tìm thấy 'Add rate' button: {e}")

            # 6b. Add international rate 2
            try:
                # Tìm tất cả các element "Add rate" và chọn element cuối cùng
                add_rate_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//span[contains(@class, 'Polaris-Text') and contains(text(), 'Add rate')]"))
                )

                if add_rate_buttons:
                    # Lấy element cuối cùng
                    add_rate_button = add_rate_buttons[-1]
                    highlight_element(driver, add_rate_button)
                    driver.execute_script("arguments[0].click();", add_rate_button)
                    delay(0.5)
                else:
                    raise Exception("No 'Add rate' button found")

                # Đợi modal mở ra
                try:
                    modal = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                    )
                    delay(0.5)

                    # Tìm select element thứ 2 và chọn option thứ 2
                    try:
                        # Tìm tất cả select elements trong modal
                        select_elements = modal.find_elements(By.TAG_NAME, "select")

                        if len(select_elements) >= 2:
                            select_element = select_elements[1]
                            highlight_element(driver, select_element)

                            # Lấy tất cả options và chọn option thứ 2
                            options = select_element.find_elements(By.TAG_NAME, "option")
                            if len(options) >= 2:
                                driver.execute_script("arguments[0].selectedIndex = 1; arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_element)
                                delay(1)
                            else:
                                print(f"⚠️ Chỉ có {len(options)} option(s), không đủ để chọn option thứ 2")
                        else:
                            print(f"⚠️ Chỉ có {len(select_elements)} select element(s), không đủ để chọn select thứ 2")
                    except Exception as e:
                        print(f"⚠️ Không tìm thấy select element thứ 2: {e}")

                    # Tìm và click button "Done"
                    try:
                        done_button = None

                        # Thử nhiều cách tìm button "Done"
                        try:
                            done_button = modal.find_element(By.XPATH, ".//button[contains(text(), 'Done')]")
                        except:
                            pass

                        if not done_button:
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[.//*[contains(text(), 'Done')]]")
                            except:
                                pass

                        if not done_button:
                            try:
                                done_button = modal.find_element(By.XPATH, ".//button[normalize-space()='Done' or .//*[normalize-space()='Done']]")
                            except:
                                pass

                        if not done_button:
                            # Tìm tất cả buttons và kiểm tra text
                            all_buttons = modal.find_elements(By.TAG_NAME, "button")
                            for btn in all_buttons:
                                btn_text = btn.text.strip().lower()
                                if 'done' in btn_text:
                                    done_button = btn
                                    break

                        if done_button:
                            highlight_element(driver, done_button)
                            driver.execute_script("arguments[0].click();", done_button)
                            delay(1)

                            # Đợi modal đóng
                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
                                )
                                delay(0.5)
                            except Exception as e:
                                print(f"⚠️ Không thể xác nhận modal đã đóng: {e}")
                                delay(0.5)
                        else:
                            print("⚠️ Không tìm thấy button 'Done'")

                    except Exception as e:
                        print(f"⚠️ Lỗi khi tìm button 'Done': {e}")

                except Exception as e:
                    print(f"⚠️ Không tìm thấy modal: {e}")

            except Exception as e:
                print(f"⚠️ Không tìm thấy 'Add rate' button ở step #6b: {e}")

            # Sau khi hoàn thành tất cả các delete, gọi hàm click_save_button
            click_save_button(driver)

        except Exception as e:
            print(f"⚠️ Không tìm thấy element 'General shipping rates': {e}")
            return

    except Exception as e:
        print(f"❌ Lỗi khi setup shipping zones: {e}")
        print("="*60)