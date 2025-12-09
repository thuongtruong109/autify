from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button
from utils.toast import show_toast

async def setup_notifications(driver: webdriver.Chrome, storeId: str, domain: str, clf_token: str, clf_email: str, clf_key: str):
    show_toast(driver, "🌐 Bắt đầu setup notifications...")

    try:
        domains_url = f"https://admin.shopify.com/store/{storeId}/settings/notifications"
        driver.get(domains_url)
        delay(3)

        # Wait for page to load completely
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
            show_toast(driver, "✅ Tìm thấy input email")

            # Click to focus
            sender_email_input.click()
            delay(1)

            # Clear existing value
            driver.execute_script("arguments[0].value = '';", sender_email_input)

            # Fill with support@domain
            sender_email_input.send_keys(f"support@{domain}")
            show_toast(driver, "✅ Đã điền email")

            click_save_button(driver)
            delay(2)

        except Exception as e:
            print(f"❌ Lỗi khi tìm hoặc điền input senderEmail: {e}")

        # setting up routing rules
        from libs.cloudflare import CloudflareClient

        async with CloudflareClient(clf_token) as cf:
            show_toast(driver, "Đang bật email routing...")
            result = await cf.enable_email_routing(domain, clf_email, clf_key)
            print("Enable Email Routing result:", result)

            accounts = await cf.get_accounts()
            print("Accounts:", accounts)

            if accounts:
                account_id = accounts[0]["id"]
                show_toast(driver, "Đang tạo destination email...")
                dest_result = await cf.create_destination_email(account_id, clf_email, clf_key)
                print("Destination Email Created:", dest_result)

            await cf.update_catch_all_email_rule(domain, clf_email, clf_key)
            show_toast(driver, "✅ Đã setup xong catch all rule!")

        # Find and click Resend verification button
        try:
            resend_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Resend verification']"))
            )
            highlight_element(driver, resend_button)
            resend_button.click()
            show_toast(driver, "✅ Đã gửi verification mail")
            delay(2)
        except Exception as e:
            print(f"❌ Lỗi khi tìm hoặc click button Resend verification: {e}")

    except Exception as e:
        print(f"❌ Error in setup notification: {e}")
        import traceback
        traceback.print_exc()