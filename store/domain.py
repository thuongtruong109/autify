from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element
from utils.toast import show_toast

async def connect_domain(driver: webdriver.Chrome, storeId: str, domain: str, clf_token: str):
    print("\n" + "="*60)
    print("🌐 CONNECT EXISTING DOMAIN...")
    print("="*60)

    show_toast(driver, "🌐 Bắt đầu connect domain...")

    try:
        domains_url = f"https://admin.shopify.com/store/{storeId}/settings/domains"
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

        # 3. Find and click "Connect existing" button
        print("🔍 Tìm và click button 'Connect existing'...")
        show_toast(driver, "🔍 Tìm và click button 'Connect existing'...")
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
        show_toast(driver, "🔍 Tìm và click button 'Next'...")
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

        # 6. Manual setup
        show_toast(driver, "🌐 Đang tìm DNS...")

        print("🔍 Tìm và click 'Manual setup'...")
        try:
            manual_setup_span = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//span[contains(@class, 'Polaris-Text--root') and contains(@class, 'Polaris-Text--bodyMd') and contains(text(), 'Manual setup')]"
                ))
            )
            highlight_element(driver, manual_setup_span)
            driver.execute_script("arguments[0].click();", manual_setup_span)
            print("✅ Đã click vào 'Manual setup'")
            delay(2)
        except Exception as e:
            print(f"❌ Không tìm thấy 'Manual setup': {e}")
            return

        print("🔍 Tìm table DNS records...")
        try:
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "table.Polaris-IndexTable__Table.Polaris-IndexTable__Table--unselectable.Polaris-IndexTable__Table--sticky"
                ))
            )
            print("✅ Đã tìm thấy table DNS records")
            delay(1)

            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")

            a_row = rows[0].find_elements(By.TAG_NAME, "td")
            a_record = a_row[4].text.strip()

            cname_row = rows[1].find_elements(By.TAG_NAME, "td")
            cname_record = cname_row[4].text.strip()

            from libs.cloudflare import CloudflareClient
            dns_records = [
                { "type": "A", "name": "@", "content": a_record, "ttl": 1, "proxied": False },
                { "type": "CNAME", "name": "www", "content": cname_record, "ttl": 1, "proxied": False },

                { "type": "TXT", "name": domain, "content": "v=spf1 -all", "ttl": 1},
                { "type": "TXT", "name": "*._domainkey", "content": "v=DKIM1; p=", "ttl": 1},
                { "type": "TXT", "name": "_dmarc", "content": "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s;", "ttl": 1}
            ]

            async with CloudflareClient(clf_token) as cf:
                results = await cf.add_multiple_dns_records(domain, dns_records)
                print(results)
                show_toast(driver, "✅ Đã thêm DNS records")
                result = await cf.enable_dnssec(domain)
                print("Enable DNSSEC result:", result)
                show_toast(driver, "✅ Đã bật DNSSEC")

            print("\n" + "="*60)
            print("✅ Đã in xong thông tin DNS records!")

        except Exception as e:
            print(f"❌ Không tìm thấy table hoặc không đọc được dữ liệu: {e}")
            import traceback
            traceback.print_exc()
            return

        # 7. Find and click "I updated DNS records" button
        print("\n🔍 Tìm và click 'I updated DNS records'...")
        show_toast(driver, "🔍 Tìm button 'I updated DNS records'...")
        try:
            updated_dns_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//span[contains(@class, 'Polaris-Text--root') and contains(@class, 'Polaris-Text--bodySm') and contains(@class, 'Polaris-Text--medium') and contains(text(), 'I updated DNS records')]"
                ))
            )
            highlight_element(driver, updated_dns_btn)
            driver.execute_script("arguments[0].click();", updated_dns_btn)
            print("✅ Đã click vào 'I updated DNS records'")
            show_toast(driver, "✅ Đã click 'I updated DNS records'!")
            delay(2)
        except Exception as e:
            print(f"❌ Không tìm thấy button 'I updated DNS records': {e}")
            import traceback
            traceback.print_exc()
            return

    except Exception as e:
        print(f"❌ Lỗi trong quá trình connect domain: {e}")
        import traceback
        traceback.print_exc()
