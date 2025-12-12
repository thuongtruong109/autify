import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from utils.element import highlight_element

"""
CAPTCHA AUTO-HANDLING ARCHITECTURE
===================================

BACKGROUND THREAD (Captcha Monitor):
    └─> Liên tục check captcha mỗi 2s (silent)
    └─> KHI PHÁT HIỆN CAPTCHA:
        1. Lock để tránh xử lý trùng
        2. Can thiệp vào driver để xử lý captcha
        3. Retry đến khi captcha được giải quyết
        4. Release lock và tiếp tục monitor

MAIN THREAD (Login/Tasks):
    └─> Chạy logic bình thường
    └─> KHÔNG CẦN gọi bất kỳ wait/check function nào
    └─> Viết code như không có captcha
    └─> Driver operations tự động đợi khi captcha đang được xử lý

FLOW DIAGRAM:
    Main Thread                    Background Thread
        |                                 |
        ├─ navigate(url)                  ├─ (check...) ✓ no captcha
        ├─ fill_email()                   ├─ (check...) ✓ no captcha
        ├─ click_button()                 ├─ (check...) ⚠️ CAPTCHA!
        |                                 ├─ 🔒 LOCK + handle captcha
        ├─ fill_password() ⏸️              |    (blocking monitor only)
        |    (đợi driver available)       ├─ captcha solving...
        |    (tự động - không code gì)    ├─ captcha solved! ✓
        ├─ ▶️ tiếp tục tự động             ├─ 🔓 UNLOCK
        ├─ click_login()                  ├─ (check...) ✓ no captcha
        └─ ...                            └─ ...

✅ MAIN THREAD CHẠY TỰ DO - KHÔNG CẦN QUAN TÂM CAPTCHA!
✅ MONITOR TỰ ĐỘNG XỬ LÝ - MỌI THỨ DIỄN RA TỰ NHIÊN!
✅ 2 LUỒNG ĐỘC LẬP - KHÔNG EXPLICIT PAUSE/RESUME!
"""

# Global state cho captcha monitor
_captcha_monitor_active = False
_captcha_monitor_thread = None
_captcha_being_handled = threading.Event()  # Signal: captcha đang được xử lý
_captcha_resolved = threading.Event()       # Signal: captcha đã được giải quyết
_captcha_lock = threading.Lock()            # Lock để tránh xử lý captcha trùng lặp

def cloudflare_captcha(driver: webdriver.Chrome, verbose: bool = True, detect_only: bool = False) -> bool:
    """
    Xử lý Cloudflare captcha bằng cách tìm <h1> chứa text "Your connection needs to be verified"
    và thực hiện các thao tác click như trong test_cf_xpath.py.

    Args:
        detect_only: Nếu True, chỉ detect captcha và return (không xử lý)
                     Nếu False, detect và XỬ LÝ captcha (loop + reload)

    Returns:
        True nếu tìm thấy và xử lý xong captcha (hoặc chỉ tìm thấy nếu detect_only=True)
        False nếu không tìm thấy captcha
    """
    import random
    from selenium.webdriver.common.action_chains import ActionChains

    def find_h1_element(text_to_find):
        """Tìm <h1> chứa text, trả về element hoặc None."""
        try:
            return driver.find_element(By.XPATH, f"//h1[contains(text(), '{text_to_find}')]")
        except:
            return None

    def wait_until_h1_appears(text_to_find, timeout=20, interval=0.3):
        """Poll liên tục cho đến khi H1 xuất hiện hoặc hết timeout."""
        if verbose:
            print("⏳ Chờ Cloudflare H1 xuất hiện...")

        start = time.time()
        while time.time() - start < timeout:
            el = find_h1_element(text_to_find)
            if el:
                if verbose:
                    print("🎉 Cloudflare H1 đã xuất hiện!")
                return el
            time.sleep(interval)

        if verbose:
            print("⏳ Cloudflare H1 KHÔNG xuất hiện trong thời gian quy định")
        return None

    def click_offset_with_marker(x, y):
        """Click vật lý tại (x,y) và tạo marker đỏ."""
        actions = ActionChains(driver)
        actions.move_by_offset(x, y).click().perform()
        actions.reset_actions()

        js_marker = f"""
        const marker = document.createElement('div');
        marker.style.position = 'absolute';
        marker.style.left = '{x-5}px';
        marker.style.top = '{y-5}px';
        marker.style.width = '10px';
        marker.style.height = '10px';
        marker.style.background='red';
        marker.style.borderRadius='50%';
        marker.style.zIndex='9999';
        document.body.appendChild(marker);
        """
        driver.execute_script(js_marker)

    try:
        # Check xem driver còn sống không
        try:
            _ = driver.current_url  # Test connection
        except Exception as e:
            if verbose:
                print(f"⚠️ Driver không khả dụng: {str(e)[:50]}")
            return False

        text_to_find = "Your connection needs to be verified"
        disappeared_count = 0  # đếm số lần không thấy element

        # Cấu hình
        offset_x = -180
        offset_y = 60
        random_clicks = 6
        random_range = 25
        random_click_delay = (0.8, 1.5)

        # ===== MODE 1: CHỈ DETECT (cho background monitor) =====
        if detect_only:
            element = find_h1_element(text_to_find)
            if element:
                if verbose:
                    print("⚠️ [DETECT] Phát hiện Cloudflare captcha!")
                return True
            return False

        # ===== MODE 2: XỬ LÝ CAPTCHA (LOOP + RELOAD) =====
        if verbose:
            print("\n🔎 BẮT ĐẦU XỬ LÝ CLOUDFLARE CAPTCHA 🔎")

        # MAIN LOOP - giống logic cũ
        while True:
            if verbose:
                print("\n🔄 Kiểm tra captcha...")

            # Poll xem H1 có xuất hiện sau page load không
            element = wait_until_h1_appears(text_to_find, timeout=20)

            # Nếu element không xuất hiện → check tiếp nhiều lần
            if not element:
                disappeared_count += 1
                if verbose:
                    print(f"⚠ Không thấy Cloudflare element (lượt {disappeared_count}/3)")

                if disappeared_count >= 3:
                    if verbose:
                        print("✅ XÁC NHẬN Cloudflare element biến mất → CAPTCHA ĐÃ ĐƯỢC GIẢI QUYẾT!")
                    return True

                if verbose:
                    print("🔄 Reload để kiểm tra lại...")
                driver.refresh()
                time.sleep(3)
                continue

            # Nếu thấy → reset counter
            disappeared_count = 0

            if verbose:
                print("⚠️ PHÁT HIỆN Cloudflare captcha - bắt đầu xử lý!")

            # Tô viền vàng element
            try:
                highlight_element(driver, element, "yellow")
                if verbose:
                    print("✨ Cloudflare element được tô viền vàng!")
            except:
                pass

            rect = element.rect
            base_x = rect['x'] + rect['width'] / 2
            base_y = rect['y'] + rect['height'] / 2

            # Random click × N lần
            for _ in range(random_clicks):
                rand_x = base_x + random.randint(-random_range, random_range)
                rand_y = base_y + random.randint(-random_range, random_range)
                click_offset_with_marker(rand_x, rand_y)
                if verbose:
                    print(f"🎯 Random click tại ({rand_x:.0f},{rand_y:.0f})")
                time.sleep(random.uniform(*random_click_delay))

            # CLICK THẬT TẠI OFFSET
            click_x = base_x + offset_x
            click_y = base_y + offset_y
            click_offset_with_marker(click_x, click_y)
            if verbose:
                print(f"🖱 CLICK THẬT tại ({click_x:.0f},{click_y:.0f})")

            # RELOAD SAU CLICK THẬT
            if verbose:
                print("⏱ Đợi 8s rồi reload...")
            time.sleep(8)
            if verbose:
                print("🔄 Reload page để kiểm tra kết quả")
            driver.refresh()
            time.sleep(2)

    except Exception as e:
        if verbose:
            print(f"⚠️ Lỗi khi xử lý Cloudflare captcha: {e}")
        return False

def _captcha_monitor_background(driver: webdriver.Chrome, check_interval: float = 2.0):
    """
    Background thread tự động DETECT và XỬ LÝ captcha - HOÀN TOÀN ĐỘC LẬP.

    Main thread chạy bình thường, KHÔNG CẦN đợi hay check gì cả.
    Monitor này tự động:
    1. Phát hiện captcha
    2. CAN THIỆP ngay vào driver để xử lý
    3. Main thread tiếp tục sau khi captcha được giải quyết

    KHÔNG có explicit pause/resume - tự nhiên như không có captcha!
    """
    global _captcha_monitor_active, _captcha_being_handled, _captcha_resolved, _captcha_lock

    print("\n" + "="*70)
    print("🔄 CAPTCHA AUTO-MONITOR ĐÃ BẮT ĐẦU")
    print(f"   💡 Main thread chạy bình thường - KHÔNG bị block!")
    print("="*70 + "\n")

    check_count = 0
    consecutive_errors = 0
    max_consecutive_errors = 5

    while _captcha_monitor_active:
        check_count += 1

        # Log mỗi 30 lần check (giảm spam hơn nữa)
        if check_count % 30 == 1:
            print(f"🔍 [Monitor] Background check #{check_count} - Main thread đang chạy tự do...")

        try:
            # 🔍 KIỂM TRA DRIVER CÒN SỐNG KHÔNG
            try:
                _ = driver.current_url
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\n⚠️ [Monitor] Driver không còn khả dụng sau {max_consecutive_errors} lần thử.")
                    print("⚠️ [Monitor] Dừng monitor.")
                    break
                time.sleep(check_interval)
                continue

            # DETECT captcha (silent - không log nếu không có)
            cf_detected = False
            shopify_detected = False

            try:
                cf_detected = cloudflare_captcha(driver, verbose=False, detect_only=True)
            except Exception:
                pass  # Silent fail

            try:
                shopify_detected = shopify_captcha(driver, verbose=False, auto_solve=False)
            except Exception:
                pass  # Silent fail

            # CHỈ KHI PHÁT HIỆN CAPTCHA → MỚI CAN THIỆP
            if cf_detected or shopify_detected:
                # Acquire lock để tránh xử lý trùng
                if _captcha_lock.acquire(blocking=False):
                    try:
                        captcha_type = "Cloudflare" if cf_detected else "Shopify"
                        print(f"\n" + "🚨"*35)
                        print(f"⚠️ [Monitor] PHÁT HIỆN {captcha_type.upper()} CAPTCHA!")
                        print(f"🔧 [Monitor] Bắt đầu xử lý tự động...")
                        print("🚨"*35 + "\n")

                        # Set event (cho trường hợp main thread muốn check)
                        _captcha_being_handled.set()
                        _captcha_resolved.clear()

                        # XỬ LÝ CAPTCHA NGAY (blocking monitor thread, KHÔNG block main thread)
                        if cf_detected:
                            success = cloudflare_captcha(driver, verbose=True, detect_only=False)
                        else:
                            success = shopify_captcha(driver, verbose=True, auto_solve=True)

                        if success:
                            print(f"\n" + "✅"*35)
                            print(f"✅ [Monitor] {captcha_type} captcha ĐÃ ĐƯỢC GIẢI QUYẾT!")
                            print(f"▶️ [Monitor] Main thread tiếp tục chạy bình thường...")
                            print("✅"*35 + "\n")
                        else:
                            print(f"⚠️ [Monitor] {captcha_type} captcha chưa giải quyết hoàn toàn\n")

                        # Clear events
                        _captcha_being_handled.clear()
                        _captcha_resolved.set()

                    finally:
                        _captcha_lock.release()

        except Exception as e:
            # Silent - chỉ log lỗi nghiêm trọng
            if "invalid session id" in str(e).lower() or "chrome not reachable" in str(e).lower():
                print(f"⚠️ [Monitor] Driver lost connection: {str(e)[:60]}")
                break

        # Chờ trước khi check lại
        time.sleep(check_interval)

    print("\n" + "="*70)
    print("🛑 CAPTCHA MONITOR ĐÃ DỪNG")
    print(f"   📊 Tổng số lần check: {check_count}")
    print("="*70 + "\n")

def start_captcha_monitor(driver: webdriver.Chrome, check_interval: float = 2.0):
    """
    Khởi động background thread để TỰ ĐỘNG PHÁT HIỆN VÀ XỬ LÝ captcha.

    ⚠️ QUAN TRỌNG:
    - Gọi hàm này NGAY SAU KHI setup driver, TRƯỚC KHI thực hiện bất kỳ task nào
    - Monitor chạy trong background thread riêng biệt, KHÔNG block main thread
    - Khi phát hiện captcha, monitor sẽ:
      1. Gửi tín hiệu pause đến main thread
      2. Tự động xử lý captcha
      3. Gửi tín hiệu resume để main thread tiếp tục

    Main thread cần gọi wait_if_captcha_being_handled() ở các điểm quan trọng
    để đồng bộ với captcha handling.

    Args:
        driver: Selenium WebDriver instance
        check_interval: Thời gian giữa các lần check (giây). Mặc định 2.0s

    Example:
        driver = setup_driver()
        start_captcha_monitor(driver, check_interval=2.0)  # Bắt đầu auto-monitor

        # Main logic
        wait_if_captcha_being_handled()  # Pause nếu có captcha
        do_something()

        wait_if_captcha_being_handled()  # Pause nếu có captcha
        do_something_else()

        stop_captcha_monitor()  # Dừng monitor khi kết thúc
    """
    global _captcha_monitor_active, _captcha_monitor_thread, _captcha_being_handled, _captcha_resolved

    # Nếu thread đã chạy, không khởi động lại
    if _captcha_monitor_active and _captcha_monitor_thread and _captcha_monitor_thread.is_alive():
        print("ℹ️ Captcha monitor đã đang chạy.")
        return

    # Reset events
    _captcha_being_handled.clear()
    _captcha_resolved.clear()

    _captcha_monitor_active = True
    _captcha_monitor_thread = threading.Thread(
        target=_captcha_monitor_background,
        args=(driver, check_interval),
        daemon=True  # Daemon thread sẽ tự động kết thúc khi program exit
    )
    _captcha_monitor_thread.start()

    # Đợi một chút để đảm bảo thread đã bắt đầu chạy
    time.sleep(0.5)
    print("✅ Captcha auto-monitor đã khởi động trong background!")
    print("💡 Main thread chạy tự do - Monitor tự động xử lý captcha khi cần!")


def stop_captcha_monitor():
    """
    Dừng background thread kiểm tra captcha.

    ⚠️ QUAN TRỌNG: Chỉ nên gọi hàm này khi:
    - Kết thúc toàn bộ chương trình / tất cả tasks
    - Chuẩn bị đóng driver/browser
    - Cleanup resources

    KHÔNG nên dừng monitor giữa chừng các tasks vì captcha có thể xuất hiện bất cứ lúc nào.
    """
    global _captcha_monitor_active, _captcha_monitor_thread

    if _captcha_monitor_active:
        print("⏳ Đang dừng captcha monitor...")
        _captcha_monitor_active = False

        # Đợi thread kết thúc (timeout 5s)
        if _captcha_monitor_thread:
            _captcha_monitor_thread.join(timeout=5)

        print("✅ Captcha monitor đã dừng.")

def extract_hcaptcha_iframe_attributes(driver: webdriver.Chrome, verbose: bool = True) -> dict:
    """
    Tìm và extract sitekey và origin từ hCaptcha iframe src.
    Trả về dictionary chứa sitekey và origin hoặc None nếu không tìm thấy.
    """
    try:
        if verbose:
            print("🔍 Đang tìm hCaptcha iframe...")

        # Tìm tất cả iframe có chứa hcaptcha
        hcaptcha_iframes = driver.find_elements(
            By.CSS_SELECTOR,
            'iframe[src*="hcaptcha.com"], iframe[data-hcaptcha-widget-id]'
        )

        if not hcaptcha_iframes:
            if verbose:
                print("⚠️ Không tìm thấy hCaptcha iframe.")
            return None

        if verbose:
            print(f"✅ Tìm thấy {len(hcaptcha_iframes)} hCaptcha iframe(s).")

        # Extract sitekey và origin từ iframe đầu tiên
        for idx, iframe in enumerate(hcaptcha_iframes):
            try:
                # Get src attribute
                src = iframe.get_attribute('src')

                if not src or 'hcaptcha.com' not in src:
                    continue

                if verbose:
                    print(f"\n{'='*60}")
                    print(f"hCaptcha iframe #{idx + 1}")
                    print(f"{'='*60}")

                # Parse URL để lấy parameters
                from urllib.parse import urlparse, parse_qs, unquote

                # Tách phần fragment (sau dấu #)
                if '#' in src:
                    base_url, fragment = src.split('#', 1)
                    # Parse fragment như query string
                    params = {}
                    for param in fragment.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = unquote(value)

                    # Extract sitekey và origin
                    sitekey = params.get('sitekey', 'N/A')
                    origin = params.get('origin', 'N/A')

                    if verbose:
                        print(f"sitekey: {sitekey}")
                        print(f"origin: {origin}")
                        print(f"{'='*60}\n")

                    # Trả về dict với sitekey và origin
                    return {
                        'sitekey': sitekey,
                        'origin': origin
                    }

            except Exception as e:
                print(f"⚠️ Lỗi khi parse iframe #{idx + 1}: {e}")
                continue

        return None

    except Exception as e:
        print(f"❌ Lỗi khi extract hCaptcha iframe attributes: {e}")
        return None

def shopify_captcha(driver: webdriver.Chrome, verbose: bool = True, auto_solve: bool = False) -> bool:
    """
    Tìm và click vào Shopify captcha 'I am human' checkbox.
    Tìm kiếm trong DOM thông thường, iframe, và shadow root.
    Nếu auto_solve=True, sẽ tự động giải captcha bằng Bright Data.
    """
    # DETECT VÀ PRINT hCaptcha iframe attributes (chỉ khi verbose=True)
    if verbose:
        print("\n🔍 Detecting hCaptcha iframe...")
    captcha_info = extract_hcaptcha_iframe_attributes(driver, verbose=verbose)
    if verbose:
        print("")

    # Nếu tìm thấy hCaptcha và auto_solve được bật, giải captcha tự động
    if captcha_info and auto_solve:
        try:
            import json
            from captcha import solve_shopify_hcaptcha, BrightCaptchaSolver

            # Đọc config để lấy Bright Data credentials
            try:
                with open('env.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    bright_config = config.get('bright_data', {})

                    if bright_config.get('enabled'):
                        api_key = bright_config.get('api_key')
                        zone = bright_config.get('zone')
                        origin = captcha_info.get('origin')

                        if api_key and origin:
                            print("🤖 Bright Data Web Unlocker được bật. Đang tự động bypass hCaptcha...")

                            # Gọi captcha.py để lấy HTML đã bypass
                            html_content = solve_shopify_hcaptcha(origin, api_key, zone)

                            if html_content:
                                # Inject HTML vào driver
                                solver = BrightCaptchaSolver(api_key, zone)
                                if solver.inject_html_to_driver(driver, html_content):
                                    print("✅ Đã bypass và inject HTML thành công!")
                                    return True
                                else:
                                    print("⚠️ Lấy được HTML nhưng inject thất bại. Chuyển sang phương thức thủ công...")
                            else:
                                print("⚠️ Tự động bypass captcha thất bại. Chuyển sang phương thức thủ công...")
                        else:
                            print("⚠️ Thiếu Bright Data API key hoặc origin URL. Chuyển sang phương thức thủ công...")
                    else:
                        if verbose:
                            print("ℹ️ Bright Data không được bật. Sử dụng phương thức thủ công...")
            except FileNotFoundError:
                if verbose:
                    print("⚠️ Không tìm thấy env.json. Chuyển sang phương thức thủ công...")
            except Exception as e:
                if verbose:
                    print(f"⚠️ Lỗi khi đọc config: {e}. Chuyển sang phương thức thủ công...")
        except ImportError:
            if verbose:
                print("⚠️ Không tìm thấy module captcha.py. Chuyển sang phương thức thủ công...")
        except Exception as e:
            if verbose:
                print(f"⚠️ Lỗi khi giải captcha tự động: {e}. Chuyển sang phương thức thủ công...")

    # 2. Tìm trong các iframe
    try:
        if verbose:
            print("   🔍 Đang tìm trong iframe...")

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if verbose:
            print(f"   Tìm thấy {len(iframes)} iframe(s).")

        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                if verbose:
                    print(f"   Đang kiểm tra iframe {i+1}/{len(iframes)}...")

                # Tìm element trong iframe
                human_elements = driver.find_elements(
                    By.XPATH,
                    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i am human')]"
                )

                if human_elements:
                    for elem in human_elements:
                        try:
                            if elem.is_displayed():
                                if verbose:
                                    print(f"   ✅ Tìm thấy 'I am human' trong iframe {i+1}.")
                                elem.click()
                                driver.switch_to.default_content()
                                return True
                        except:
                            continue

                # Thử tìm checkbox hoặc button thông thường
                checkbox_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    'input[type="checkbox"], div[role="checkbox"], button[role="checkbox"]'
                )

                for elem in checkbox_elements:
                    try:
                        if elem.is_displayed():
                            parent_text = driver.execute_script("return arguments[0].parentElement.textContent;", elem).lower()
                            if 'human' in parent_text or 'verify' in parent_text:
                                if verbose:
                                    print(f"   ✅ Tìm thấy checkbox xác minh trong iframe {i+1}.")
                                elem.click()
                                driver.switch_to.default_content()
                                return True
                    except:
                        continue

                driver.switch_to.default_content()

            except Exception as e:
                if verbose:
                    print(f"   ⚠️ Lỗi khi kiểm tra iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Lỗi khi tìm trong iframe: {e}")

    # 3. Tìm trong shadow root
    try:
        if verbose:
            print("   🔍 Đang tìm trong shadow root...")

        # Tìm tất cả elements có shadow root
        elements_with_shadow = driver.execute_script("""
            function findInShadowRoots(root = document.body) {
                let results = [];
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
                let node;
                while (node = walker.nextNode()) {
                    if (node.shadowRoot) {
                        results.push(node);
                    }
                }
                return results;
            }
            return findInShadowRoots();
        """)

        if verbose:
            print(f"   Tìm thấy {len(elements_with_shadow)} element(s) có shadow root.")

        for elem in elements_with_shadow:
            try:
                # Tìm trong shadow root
                shadow_elements = driver.execute_script("""
                    const shadowRoot = arguments[0].shadowRoot;
                    if (!shadowRoot) return [];
                    const allElements = shadowRoot.querySelectorAll('*');
                    return Array.from(allElements).filter(el =>
                        el.textContent.toLowerCase().includes('i am human') ||
                        el.textContent.toLowerCase().includes('verify') ||
                        el.getAttribute('aria-label')?.toLowerCase().includes('human')
                    );
                """, elem)

                if shadow_elements:
                    for shadow_elem in shadow_elements:
                        try:
                            if driver.execute_script("return arguments[0].offsetParent !== null;", shadow_elem):
                                if verbose:
                                    print("   ✅ Tìm thấy 'I am human' trong shadow root.")
                                driver.execute_script("arguments[0].click();", shadow_elem)
                                return True
                        except:
                            continue
            except Exception as e:
                continue
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Lỗi khi tìm trong shadow root: {e}")

    if verbose:
        print("   ⚠️ Không tìm thấy Shopify captcha 'I am human' ở bất kỳ đâu.")
    return False