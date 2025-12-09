from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button
from utils.toast import show_toast

async def setup_notifications(driver: webdriver.Chrome, storeId: str, domain: str, cloudflare_token: str):
    print("\n" + "="*60)
    print("🌐 SETUP NOTIFICATIONS...")
    print("="*60)

    show_toast(driver, "🌐 Bắt đầu connect domain...")

    try:
        domains_url = f"https://admin.shopify.com/store/{storeId}/settings/notifications"
        print(f"Đang vào trang: {domains_url}")
        driver.get(domains_url)
        delay(3)

        # 2. Wait for page to load completely
        print("⏳ Đợi trang load xong...")
        show_toast(driver, "⏳ Đợi trang load xong...")
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        delay(2)

        # Find the sender email input field
        show_toast(driver, "🔍 Tìm element input senderEmail...")
        try:
            sender_email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "senderEmail"))
            )
            highlight_element(driver, sender_email_input)
            print("✅ Tìm thấy input senderEmail")
            show_toast(driver, "✅ Tìm thấy input senderEmail")

            # Click to focus
            sender_email_input.click()
            delay(1)

            # Clear existing value
            driver.execute_script("arguments[0].value = '';", sender_email_input)

            # Fill with support@domain
            support_email = f"support@{domain}"
            sender_email_input.send_keys(support_email)
            print(f"✅ Đã điền email: {support_email}")
            show_toast(driver, f"✅ Đã điền email: {support_email}")

            click_save_button(driver)
            delay(2)

            # Find and click Resend verification button
            try:
                resend_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Resend verification']"))
                )
                highlight_element(driver, resend_button)
                resend_button.click()
                show_toast(driver, "✅ Đã click Resend verification")
                delay(2)
            except Exception as e:
                print(f"❌ Lỗi khi tìm hoặc click button Resend verification: {e}")

        except Exception as e:
            print(f"❌ Lỗi khi tìm hoặc điền input senderEmail: {e}")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình setup notification: {e}")
        import traceback
        traceback.print_exc()