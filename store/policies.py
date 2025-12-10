from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Dict, Any
from utils.element import delay, highlight_element

def setup_legal_policies(driver: webdriver.Chrome, storeId: str, policies: Dict[str, Any]):
    legal_pages = [
        {
            "name": "Refund Policy",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/refund",
            "policy_key": "return_and_refund"
        },
        {
            "name": "Terms of Service",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/terms-of-service",
            "policy_key": "terms_of_service"
        },
        {
            "name": "Shipping Policy",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/shipping",
            "policy_key": "shipping"
        },
        {
            "name": "Contact Information",
            "url": f"https://admin.shopify.com/store/{storeId}/settings/legal/contact-information",
            "policy_key": "contact_information"
        }
    ]

    try:
        for page in legal_pages:
            print(f"\n📋 Đang xử lý: {page['name']}...")
            print(f"URL: {page['url']}")

            # Vào trang policy
            driver.get(page['url'])
            delay(2)

            # Lấy nội dung policy từ GUI
            policy_content = policies.get(page['policy_key'], '').strip()
            if policy_content:
                print(f"📝 Đang nhập nội dung policy cho {page['name']}...")

                # Tìm textarea để nhập nội dung
                # Thử các selector phổ biến cho Shopify admin
                textarea_selectors = [
                    "textarea[name='policy[content]']",
                    "textarea[id*='policy']",
                    "textarea[class*='policy']",
                    ".policy-editor textarea",
                    ".editor textarea",
                    "textarea"
                ]

                textarea = None
                for selector in textarea_selectors:
                    try:
                        textarea = driver.find_element(By.CSS_SELECTOR, selector)
                        if textarea.is_displayed():
                            break
                    except:
                        continue

                if textarea:
                    # Xóa nội dung cũ và nhập nội dung mới
                    textarea.clear()
                    textarea.send_keys(policy_content)
                    print(f"✅ Đã nhập nội dung policy cho {page['name']}")
                    delay(1)
                else:
                    print(f"⚠️ Không tìm thấy textarea để nhập nội dung cho {page['name']}")
            else:
                print(f"⚠️ Không có nội dung policy cho {page['name']}")

            # Tìm button "Publish" và check aria-disabled mỗi 2s
            print(f"🔍 Tìm button 'Publish' cho {page['name']}...")

            max_attempts = 30  # Tối đa 30 lần check (60 giây)
            publish_clicked = False

            for attempt in range(max_attempts):
                try:
                    # Tìm button có text "Publish"
                    publish_btn = driver.find_element(
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'publish')]"
                    )

                    # Kiểm tra aria-disabled
                    aria_disabled = publish_btn.get_attribute("aria-disabled")

                    print(f"   [Attempt {attempt + 1}/{max_attempts}] Button 'Publish' - aria-disabled: {aria_disabled}")

                    if aria_disabled == "false":
                        # Button enabled, click vào
                        highlight_element(driver, publish_btn)
                        print(f"✅ Button 'Publish' đã enabled. Đang click...")
                        driver.execute_script("arguments[0].click();", publish_btn)
                        print(f"✅ Đã click button 'Publish' cho {page['name']}.")
                        publish_clicked = True
                        break
                    else:
                        # Button vẫn disabled, đợi 2s và thử lại
                        print(f"   ⏳ Button vẫn disabled. Đợi 2s...")
                        delay(2)

                except Exception as e:
                    if attempt == 0:
                        print(f"   ⚠️ Không tìm thấy button 'Publish': {e}")
                    delay(2)

            if not publish_clicked:
                print(f"⚠️ Không thể click button 'Publish' cho {page['name']} sau {max_attempts} lần thử.")

            # Đợi 1s trước khi chuyển sang trang tiếp theo
            delay(1)

        print("\n✅ HOÀN TẤT SETUP LEGAL POLICIES!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi setup legal policies: {e}")
        print("="*60)