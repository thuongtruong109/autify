from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element

def connect_domain(driver: webdriver.Chrome, storeId: str, domain: str):
    """Connect an existing domain to the Shopify store"""
    print("\n" + "="*60)
    print("🌐 CONNECT EXISTING DOMAIN...")
    print("="*60)

    try:
        # 1. Navigate to domains settings page
        domains_url = f"https://admin.shopify.com/store/{storeId}/settings/domains"
        print(f"Đang vào trang: {domains_url}")
        driver.get(domains_url)
        delay(3)

        # 2. Wait for page to load completely
        print("⏳ Đợi trang load xong...")
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        delay(2)

        # 3. Find and click "Connect existing" button
        print("🔍 Tìm và click button 'Connect existing'...")
        try:
            connect_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//button[contains(@class, 'Polaris-Button') and .//span[contains(text(), 'Connect existing')]]"
                ))
            )
            highlight_element(driver, connect_btn)
            driver.execute_script("arguments[0].click();", connect_btn)
            print("✅ Đã click vào button 'Connect existing'")
            delay(2)
        except Exception as e:
            print(f"❌ Không tìm thấy button 'Connect existing': {e}")
            return

        # 4. Wait for modal to appear and find input field
        print("⏳ Đợi modal xuất hiện...")
        try:
            modal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".Polaris-Modal-Dialog__Modal"))
            )
            delay(1)

            # Find the domain input field
            print(f"🔍 Tìm input field và điền domain: {domain}")
            domain_input = modal.find_element(
                By.CSS_SELECTOR,
                "input[name='domain'][class*='Polaris-TextField__Input']"
            )
            highlight_element(driver, domain_input)
            domain_input.clear()
            domain_input.send_keys(domain)
            print(f"✅ Đã điền domain: {domain}")
            delay(1)

        except Exception as e:
            print(f"❌ Không tìm thấy modal hoặc input field: {e}")
            return

        # 5. Find and click "Next" button in modal
        print("🔍 Tìm và click button 'Next'...")
        try:
            next_btn = modal.find_element(
                By.XPATH,
                ".//button[contains(@class, 'Polaris-Button--variantPrimary') and .//span[contains(text(), 'Next')]]"
            )
            highlight_element(driver, next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            print("✅ Đã click vào button 'Next'")
            delay(2)

            print("✅ Hoàn thành connect domain!")

        except Exception as e:
            print(f"❌ Không tìm thấy button 'Next': {e}")
            return

    except Exception as e:
        print(f"❌ Lỗi trong quá trình connect domain: {e}")
        import traceback
        traceback.print_exc()
