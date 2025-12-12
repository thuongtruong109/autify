"""
🚀 PAGES SETUP MODULE with TinyMCE Integration
===============================================

Module này setup các pages (Contact Us, About Us) với TinyMCE content injection.
Sử dụng chiến lược tương tự như policies.py để inject content vào TinyMCE editor.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, Any
from utils.element import delay, highlight_element, click_save_button
from policies import debug_tinymce_state
import time

def inject_page_content_smart(driver: webdriver.Chrome, content: str, page_name: str = "about_us") -> bool:
    """
    🚀 Inject content vào TinyMCE editor - CHỈ GIỮ STRATEGY 4 (WORK)
    """
    html_content = f"<p>{content}</p>"

    print(f"\n🚀 SMART PAGE INJECTION: {page_name}")
    print(f"   Content length: {len(content)} chars")

    # Debug TinyMCE state
    debug_tinymce_state(driver)

    # Wait for TinyMCE to load
    print(f"\n⏳ Waiting for TinyMCE...")
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return typeof tinyMCE !== 'undefined' && typeof tinymce !== 'undefined'")
        )
        print(f"   ✅ TinyMCE loaded")
    except:
        print(f"   ⚠️ TinyMCE chưa load, nhưng TIẾP TỤC thử inject!")

    # ================================================================
    # 🔥 STRATEGY 4: Direct textarea manipulation (WORK - GIỮ LẠI)
    # ================================================================
    print(f"\n🔥 Strategy 4: Direct textarea manipulation")
    result = driver.execute_script("""
        try {
            // Tìm textarea đầu tiên có TinyMCE
            var textareas = document.querySelectorAll('textarea');
            var targetTextarea = null;

            for (var i = 0; i < textareas.length; i++) {
                var ta = textareas[i];
                if (ta.id && typeof tinyMCE !== 'undefined') {
                    var editor = tinyMCE.get(ta.id);
                    if (editor) {
                        targetTextarea = ta;
                        break;
                    }
                }
            }

            if (!targetTextarea) {
                return { success: false, error: 'No textarea with TinyMCE found' };
            }

            // Set textarea value
            targetTextarea.value = arguments[0];
            targetTextarea.dispatchEvent(new Event('input', { bubbles: true }));
            targetTextarea.dispatchEvent(new Event('change', { bubbles: true }));

            // Trigger TinyMCE to load from textarea
            var editor = tinyMCE.get(targetTextarea.id);
            if (editor) {
                editor.load();
                editor.fire('change');
                editor.save();
            }

            return { success: true, method: 'textarea manipulation', textareaId: targetTextarea.id };
        } catch (e) {
            return { success: false, error: e.toString() };
        }
    """, content)

    if result.get('success'):
        print(f"   ✅ SUCCESS via {result.get('method')} (Textarea: {result.get('textareaId')})")
        time.sleep(0.5)
        return True
    else:
        print(f"   ⚠️ Strategy 4 chưa work: {result.get('error')}")
        print(f"   ⚠️ Content có thể chưa inject được, nhưng KHÔNG ĐÓNG APP!")
        return False

def setup_contact_page(driver: webdriver.Chrome, storeId: str, pages: Dict[str, str] = None):
    """
    Setup Contact Us và About Us pages với TinyMCE content

    🚀 KHÔNG BAO GIỜ TỰ ĐỘNG ĐÓNG APP KHI GẶP LỖI!
    Chỉ print warning và tiếp tục chạy.
    """
    if pages is None:
        pages = {}

    contact_content = pages.get('contact_us', '').strip()
    about_content = pages.get('about_us', '').strip()

    print(f"\n{'='*60}")
    print(f"📄 SETUP PAGES - Contact Us & About Us")
    print(f"{'='*60}")
    print(f"📝 Contact Us content: {len(contact_content)} chars")
    print(f"📝 About Us content: {len(about_content)} chars")

    pages_url = f"https://admin.shopify.com/store/{storeId}/pages"
    print(f"\n🌐 Đang vào trang: {pages_url}")
    driver.get(pages_url)
    delay(3)

    # ================================================================
    # STEP 1: Edit Contact Page
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 1: Edit Contact Page")
    print(f"{'='*60}")

    print("🔍 Tìm item có chữ 'Contact'...")

    # Tìm element có text "Contact" - WRAP trong try để không crash
    try:
        contact_item = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[text()='Contact'] | //span[text()='Contact'] | //div[text()='Contact'] | //button[text()='Contact'] | //a[contains(text(), 'Contact')] | //button[contains(text(), 'Contact')] | //span[contains(text(), 'Contact')]"))
        )

        highlight_element(driver, contact_item)
        print(f"✅ Tìm thấy item 'Contact'. Text: '{contact_item.text}'. Click...")
        driver.execute_script("arguments[0].click();", contact_item)
        delay(3)
        print("✅ Đã click vào item 'Contact'.")
    except:
        print("⚠️ Không tìm thấy item 'Contact', nhưng TIẾP TỤC chạy!")

    # Đợi page load sau khi click Contact
    delay(3)

    # ================================================================
    # STEP 2: UPDATE TITLE INPUT - CHỈ GIỮ STRATEGY 2 (WORK) 🔥
    # ================================================================
    print(f"\n🔍 STEP 2: Tìm title input và update 'Contact Us'...")

    title_updated = False

    # STRATEGY 2: Common selectors (WORK - GIỮ LẠI)
    print(f"   🔥 Strategy 2: Common selectors...")
    selectors = [
        "input[name*='title']",
        "input[id*='title']",
        "input[placeholder*='title' i]",
        "input[placeholder*='about us' i]",
        "input[placeholder*='page' i]",
        "input.Polaris-TextField__Input",
        "input[type='text']:first-of-type"
    ]

    for selector in selectors:
        try:
            title_input = driver.find_element(By.CSS_SELECTOR, selector)
            if not title_input.is_displayed():
                continue

            print(f"   ✅ Found by selector: {selector}")

            try:
                highlight_element(driver, title_input)

                # Clear và type - WRAP để tránh segmentation fault
                print(f"   🔥 Clear và type 'Contact Us'...")

                # Click input
                try:
                    title_input.click()
                    delay(0.3)
                except:
                    print(f"   ⚠️ Click failed, nhưng tiếp tục...")

                # Clear bằng JavaScript an toàn hơn
                try:
                    driver.execute_script("""
                        arguments[0].focus();
                        arguments[0].select();
                        arguments[0].value = '';
                    """, title_input)
                    delay(0.2)
                except:
                    print(f"   ⚠️ Clear failed, nhưng tiếp tục...")

                # Type "Contact Us"
                try:
                    title_input.send_keys("Contact Us")
                    delay(0.5)

                    # Tab out
                    title_input.send_keys(Keys.TAB)
                    delay(0.5)
                except Exception as e:
                    print(f"   ⚠️ Send keys failed: {e}, thử selector tiếp...")
                    continue

                # Check value
                final_value = title_input.get_attribute('value')
                print(f"   ✅ Updated to: '{final_value}'")

                if "Contact Us" in final_value:
                    title_updated = True
                    print(f"   ✅ Xác nhận: Title đã update thành công!")
                    break
                else:
                    print(f"   ⚠️ Value không khớp, thử selector tiếp theo...")

            except Exception as e:
                print(f"   ⚠️ Error updating input: {e}")
                continue

        except Exception as e:
            # Selector này không tìm thấy, thử selector tiếp theo
            print(f"   ⚠️ Selector {selector} failed: {e}")
            continue
            continue

    if not title_updated:
        print(f"   ⚠️ Could not update title input, nhưng TIẾP TỤC chạy!")

    # ================================================================
    # STEP 3: Inject Contact Us content vào TinyMCE
    # ================================================================
    if contact_content:
        print(f"\n🔍 STEP 3: Inject Contact Us content vào TinyMCE...")
        delay(2)  # Đợi TinyMCE load

        success = inject_page_content_smart(driver, contact_content, "contact_us")

        if success:
            print(f"   ✅ Đã inject Contact Us content")
        else:
            print(f"   ⚠️ Không thể inject Contact Us content, nhưng TIẾP TỤC!")
    else:
        print(f"\n⚠️ STEP 3: Không có Contact Us content để inject")

    # ================================================================
    # STEP 4: Đợi và Click Save button cho Contact page
    # ================================================================
    print(f"\n🔍 STEP 4: Đợi Save button enable và click...")

    # CANH CANH đợi button Save enable & visible
    print("   🔥 Đang canh chờ button Save enable...")
    save_clicked = False
    start_time = time.time()
    timeout = 30

    while time.time() - start_time < timeout:
        # Tìm tất cả button có chữ Save
        buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]")

        for btn in buttons:
            # Check visible
            if not btn.is_displayed():
                continue

            # Check enabled
            is_enabled = btn.is_enabled()
            aria_disabled = btn.get_attribute("aria-disabled")

            # Button phải enable VÀ aria-disabled phải "false" (hoặc None)
            if is_enabled and (aria_disabled is None or aria_disabled == "false"):
                print(f"   ✅ Tìm thấy button Save enable! Click...")
                highlight_element(driver, btn)
                driver.execute_script("arguments[0].click();", btn)
                delay(2)
                print("   ✅ Đã click Save!")
                save_clicked = True
                break

        if save_clicked:
            break

        # Chưa tìm thấy, đợi và thử lại
        delay(0.5)

    if not save_clicked:
        print("   ⚠️ Chưa click được Save button, nhưng TIẾP TỤC!")

    # ================================================================
    # PART 2: Tạo About Us Page
    # ================================================================
    print(f"\n{'='*60}")
    print(f"PART 2: Tạo About Us Page")
    print(f"{'='*60}")

    # Quay lại trang pages
    print("\n🔄 Quay lại trang pages...")
    pages_url = f"https://admin.shopify.com/store/{storeId}/pages"
    driver.get(pages_url)
    delay(3)

    # Tìm button "Add page" và click
    print("🔍 STEP 1: Tìm button 'Add page'...")

    try:
        add_page_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add page')] | //a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add page')]"))
        )

        highlight_element(driver, add_page_btn)
        print("   ✅ Tìm thấy button 'Add page'. Click...")
        driver.execute_script("arguments[0].click();", add_page_btn)
        delay(2)
        print("   ✅ Đã click 'Add page'.")
    except:
        print("   ⚠️ Không tìm thấy button 'Add page', nhưng TIẾP TỤC!")

    # Đợi page load
    delay(3)

    # ================================================================
    # STEP 2: UPDATE TITLE INPUT "About Us" - CHỈ GIỮ STRATEGY 2 (WORK) 🔥
    # ================================================================
    print(f"\n🔍 STEP 2: Tìm title input và update 'About Us'...")

    about_title_updated = False

    # STRATEGY 2: Common selectors (WORK - GIỮ LẠI)
    print(f"   🔥 Strategy 2: Common selectors...")
    selectors = [
        "input[name*='title']",
        "input[id*='title']",
        "input[placeholder*='title' i]",
        "input.Polaris-TextField__Input",
        "input[type='text']:first-of-type"
    ]

    for selector in selectors:
        try:
            title_input = driver.find_element(By.CSS_SELECTOR, selector)
            if not title_input.is_displayed():
                continue

            print(f"   ✅ Found by selector: {selector}")

            try:
                highlight_element(driver, title_input)

                # Clear và type - WRAP để tránh segmentation fault
                print(f"   🔥 Clear và type 'About Us'...")

                # Click input
                try:
                    title_input.click()
                    delay(0.3)
                except:
                    print(f"   ⚠️ Click failed, nhưng tiếp tục...")

                # Clear bằng JavaScript an toàn hơn
                try:
                    driver.execute_script("""
                        arguments[0].focus();
                        arguments[0].select();
                        arguments[0].value = '';
                    """, title_input)
                    delay(0.2)
                except:
                    print(f"   ⚠️ Clear failed, nhưng tiếp tục...")

                # Type "About Us"
                try:
                    title_input.send_keys("About Us")
                    delay(0.5)

                    # Tab out
                    title_input.send_keys(Keys.TAB)
                    delay(0.5)
                except Exception as e:
                    print(f"   ⚠️ Send keys failed: {e}, thử selector tiếp...")
                    continue

                # Check value
                final_value = title_input.get_attribute('value')
                print(f"   ✅ Updated to: '{final_value}'")

                if "About Us" in final_value:
                    about_title_updated = True
                    print(f"   ✅ Xác nhận: Title đã update thành công!")
                    break
                else:
                    print(f"   ⚠️ Value không khớp, thử selector tiếp theo...")

            except Exception as e:
                print(f"   ⚠️ Error updating input: {e}")
                continue

        except Exception as e:
            # Selector này không tìm thấy, thử selector tiếp theo
            print(f"   ⚠️ Selector {selector} failed: {e}")
            continue

    if not about_title_updated:
        print(f"   ⚠️ Could not update About Us title, nhưng TIẾP TỤC chạy!")

    # ================================================================
    # STEP 3: CLICK RADIO BUTTON 🔥
    # ================================================================
    print(f"\n🔍 STEP 3: Tìm và click radio button...")

    # Scan tất cả radio buttons và click cái đầu tiên visible
    all_radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
    visible_radios = [r for r in all_radios if r.is_displayed()]

    if visible_radios:
        radio_button = visible_radios[0]
        highlight_element(driver, radio_button)
        driver.execute_script("arguments[0].click();", radio_button)
        delay(1)
        print(f"   ✅ Clicked radio button")
    else:
        print(f"   ⚠️ Không tìm thấy radio button, nhưng TIẾP TỤC!")

    # ================================================================
    # STEP 4: Inject About Us content vào TinyMCE
    # ================================================================
    if about_content:
        print(f"\n🔍 STEP 4: Inject About Us content vào TinyMCE...")
        delay(2)  # Đợi TinyMCE load sau khi click radio

        success = inject_page_content_smart(driver, about_content, "about_us")

        if success:
            print(f"   ✅ Đã inject About Us content")
        else:
            print(f"   ⚠️ Không thể inject About Us content, nhưng TIẾP TỤC!")
    else:
        print(f"\n⚠️ STEP 4: Không có About Us content để inject")

    # ================================================================
    # STEP 5: Đợi và Click Save button cuối cùng
    # ================================================================
    print(f"\n🔍 STEP 5: Đợi Save button enable và click...")

    # CANH CANH đợi button Save enable & visible
    print("   🔥 Đang canh chờ button Save enable...")
    final_save_clicked = False
    start_time = time.time()
    timeout = 30

    while time.time() - start_time < timeout:
        # Tìm tất cả button có chữ Save
        buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]")

        for btn in buttons:
            # Check visible
            if not btn.is_displayed():
                continue

            # Check enabled
            is_enabled = btn.is_enabled()
            aria_disabled = btn.get_attribute("aria-disabled")

            # Button phải enable VÀ aria-disabled phải "false" (hoặc None)
            if is_enabled and (aria_disabled is None or aria_disabled == "false"):
                print(f"   ✅ Tìm thấy button Save enable! Click...")
                highlight_element(driver, btn)
                driver.execute_script("arguments[0].click();", btn)
                delay(2)
                print("   ✅ Đã click Save!")
                final_save_clicked = True
                break

        if final_save_clicked:
            break

        # Chưa tìm thấy, đợi và thử lại
        delay(0.5)

    if final_save_clicked:
        print(f"\n{'='*60}")
        print(f"✅ HOÀN TẤT SETUP PAGES!")
        print(f"{'='*60}")
        print(f"✅ Contact Us page: Updated với {len(contact_content)} chars")
        print(f"✅ About Us page: Created với {len(about_content)} chars")
        print(f"{'='*60}")
    else:
        print("⚠️ Chưa click được Save button, nhưng ĐÃ HOÀN TẤT!")
        print(f"{'='*60}")