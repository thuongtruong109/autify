from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button, find_button

def setup_world_market(driver: webdriver.Chrome, storeId: str):
    print("\n" + "="*60)
    print("🌍 SETUP WORLD MARKET...")
    print("="*60)

    # Vào markets page
    markets_url = f"https://admin.shopify.com/store/{storeId}/markets/new"
    driver.get(markets_url)
    delay(3)

    try:
        # 1. Tìm input field và điền "World"
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.Polaris-TextField__Input"))
        )
        input_field.clear()
        input_field.send_keys("World")
        delay(2)

        # 2. Tìm và click button "Add condition"
        add_condition_btn = find_button(driver, ["Add condition"])
        if add_condition_btn:
            highlight_element(driver, add_condition_btn)
            driver.execute_script("arguments[0].click();", add_condition_btn)
            delay(3)

            # 3. Tìm checkbox có label "Showing 237 regions" và tick vào
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
                        driver.execute_script("arguments[0].click();", checkbox)
                        delay(1)
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
                except Exception as e2:
                    print(f"⚠️ Lỗi khi tìm checkboxes: {e2}")

            # 4. Tìm và click button "Done"
            done_btn = find_button(driver, ["Done"])
            if done_btn:
                highlight_element(driver, done_btn)
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