"""
🚀 ADVANCED TINYMCE CONTENT INJECTION MODULE
============================================

Chiến lược đa tầng để inject content vào TinyMCE editor với độ tin cậy cao:

Strategy 1: TinyMCE.get(editorId).setContent()
   - Sử dụng TinyMCE API trực tiếp với ID cụ thể
   - Fastest và most reliable nếu editor đã init

Strategy 2: tinymce.activeEditor.setContent()
   - Sử dụng activeEditor API
   - Tốt cho trường hợp chỉ có 1 editor active

Strategy 3: Loop through tinyMCE.editors[]
   - Scan tất cả editors và tìm editor phù hợp
   - Fallback tốt khi không biết chính xác editor ID

Strategy 4: Direct textarea + triggerSave
   - Manipulate textarea trực tiếp
   - Trigger TinyMCE load/save để sync

Strategy 5: Iframe body manipulation (Last Resort)
   - Switch vào iframe
   - Manipulate body element trực tiếp
   - Multiple injection methods: innerHTML, execCommand, textContent

Mỗi strategy có mechanism riêng để trigger events và sync với textarea.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from typing import Dict, Any
import time
from utils.element import delay, highlight_element, find_iframe_with_selector

def debug_tinymce_state(driver: webdriver.Chrome) -> Dict[str, Any]:
    """
    🔍 Debug function để kiểm tra TinyMCE state

    Returns:
        Dictionary chứa thông tin về TinyMCE editors, iframes, textareas
    """
    try:
        result = driver.execute_script("""
            var info = {
                tinyMCE_available: typeof tinyMCE !== 'undefined',
                tinymce_available: typeof tinymce !== 'undefined',
                editors: [],
                iframes: [],
                textareas: []
            };

            // Get TinyMCE editors info
            if (typeof tinyMCE !== 'undefined' && tinyMCE.editors) {
                info.editors = tinyMCE.editors.map(function(ed) {
                    return {
                        id: ed.id,
                        initialized: ed.initialized,
                        iframeId: ed.iframeElement ? ed.iframeElement.id : null,
                        hasContent: ed.getContent().length > 0
                    };
                });
            }

            // Get all iframes
            var allIframes = document.querySelectorAll('iframe');
            info.iframes = Array.from(allIframes).map(function(ifr) {
                return {
                    id: ifr.id || 'no-id',
                    src: (ifr.src || 'no-src').substring(0, 50),
                    visible: ifr.offsetParent !== null
                };
            });

            // Get all textareas
            var allTextareas = document.querySelectorAll('textarea');
            info.textareas = Array.from(allTextareas).map(function(ta) {
                return {
                    id: ta.id || 'no-id',
                    name: ta.name || 'no-name',
                    hasValue: ta.value.length > 0
                };
            });

            return info;
        """)

        print(f"\n🔍 TinyMCE Debug Info:")
        print(f"   tinyMCE available: {result.get('tinyMCE_available')}")
        print(f"   tinymce available: {result.get('tinymce_available')}")
        print(f"   Editors count: {len(result.get('editors', []))}")
        for ed in result.get('editors', []):
            print(f"      - ID: {ed['id']}, Init: {ed['initialized']}, Iframe: {ed['iframeId']}")
        print(f"   Iframes count: {len(result.get('iframes', []))}")
        for ifr in result.get('iframes', [])[:5]:  # Show first 5
            print(f"      - ID: {ifr['id']}, Visible: {ifr['visible']}")
        print(f"   Textareas count: {len(result.get('textareas', []))}")

        return result
    except Exception as e:
        print(f"   ❌ Debug error: {e}")
        return {}

def inject_policy_content_smart(driver: webdriver.Chrome, content: str, policy_type: str = "TERMS_OF_SERVICE") -> bool:
    """
    🧠 SMART & RESILIENT CONTENT INJECTION với multi-layered fallback

    Chiến lược:
    1. TinyMCE API Direct (setContent) - FASTEST & MOST RELIABLE
    2. TinyMCE activeEditor API - Fallback 1
    3. Iframe manipulation - Fallback 2
    4. Direct DOM manipulation - Last resort

    Args:
        driver: WebDriver instance
        content: Content to inject
        policy_type: Policy type (TERMS_OF_SERVICE, REFUND_POLICY, SHIPPING_POLICY, etc.)
    """
    html_content = f"<p>{content}</p>"
    # ID của editor (không có _ifr)
    editor_id = f"rte-uplift-{policy_type.upper()}-r2e"
    iframe_id = f"{editor_id}_ifr"

    print(f"\n🚀 SMART INJECTION with TinyMCE API: Policy type = {policy_type}")
    print(f"   Editor ID: {editor_id}")
    print(f"   Iframe ID: {iframe_id}")

    # BƯỚC 1: Đảm bảo page đã load hoàn toàn
    print(f"\n⏳ Đợi page và TinyMCE load...")
    try:
        # Đợi readyState complete
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)

        # Scroll để trigger lazy-load
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(0.5)

        # Đợi TinyMCE load
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return typeof tinyMCE !== 'undefined' && typeof tinymce !== 'undefined'")
            )
            print(f"   ✅ TinyMCE loaded")
        except TimeoutException:
            print(f"   ⚠️ TinyMCE might not be loaded yet")

        print(f"   ✅ Page ready")
    except Exception as e:
        print(f"   ⚠️ Page wait warning: {e}")

    # Debug: Print TinyMCE state
    debug_tinymce_state(driver)

    # ================================================================
    # 🔥 STRATEGY 1: TinyMCE API Direct - setContent()
    # ================================================================
    print(f"\n🔥 Strategy 1: TinyMCE.get('{editor_id}').setContent()")
    try:
        result = driver.execute_script(f"""
            try {{
                // Kiểm tra TinyMCE có sẵn không
                if (typeof tinyMCE === 'undefined') {{
                    return {{ success: false, error: 'tinyMCE is undefined' }};
                }}

                // Lấy editor bằng ID
                var editor = tinyMCE.get('{editor_id}');
                if (!editor) {{
                    return {{ success: false, error: 'Editor not found with ID: {editor_id}' }};
                }}

                // Set content
                editor.setContent(arguments[0]);

                // Trigger events để đảm bảo sync
                editor.fire('change');
                editor.fire('input');
                editor.fire('keyup');

                // Save content to textarea
                editor.save();

                return {{ success: true, method: 'tinyMCE.get().setContent()' }};
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        """, html_content)

        if result.get('success'):
            print(f"   ✅ SUCCESS via {result.get('method')}")
            time.sleep(0.5)
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # ================================================================
    # 🔥 STRATEGY 2: TinyMCE activeEditor API
    # ================================================================
    print(f"\n🔥 Strategy 2: tinymce.activeEditor.setContent()")
    try:
        result = driver.execute_script("""
            try {
                // Kiểm tra tinymce có sẵn không
                if (typeof tinymce === 'undefined') {
                    return { success: false, error: 'tinymce is undefined' };
                }

                // Sử dụng activeEditor
                var editor = tinymce.activeEditor;
                if (!editor) {
                    return { success: false, error: 'No active editor' };
                }

                // Set content
                editor.setContent(arguments[0]);

                // Trigger events
                editor.fire('change');
                editor.fire('input');
                editor.fire('keyup');

                // Save
                editor.save();

                return { success: true, method: 'tinymce.activeEditor.setContent()' };
            } catch (e) {
                return { success: false, error: e.toString() };
            }
        """, html_content)

        if result.get('success'):
            print(f"   ✅ SUCCESS via {result.get('method')}")
            time.sleep(0.5)
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # ================================================================
    # 🔥 STRATEGY 3: Loop through all TinyMCE editors
    # ================================================================
    print(f"\n🔥 Strategy 3: Loop through tinyMCE.editors[]")
    try:
        result = driver.execute_script(f"""
            try {{
                if (typeof tinyMCE === 'undefined' || !tinyMCE.editors) {{
                    return {{ success: false, error: 'No editors available' }};
                }}

                // Tìm editor phù hợp
                var targetEditor = null;
                for (var i = 0; i < tinyMCE.editors.length; i++) {{
                    var editor = tinyMCE.editors[i];
                    // Kiểm tra ID hoặc iframe ID
                    if (editor.id === '{editor_id}' ||
                        editor.iframeElement?.id === '{iframe_id}' ||
                        editor.id.includes('{policy_type}')) {{
                        targetEditor = editor;
                        break;
                    }}
                }}

                if (!targetEditor && tinyMCE.editors.length > 0) {{
                    // Fallback: dùng editor đầu tiên
                    targetEditor = tinyMCE.editors[0];
                }}

                if (!targetEditor) {{
                    return {{ success: false, error: 'No suitable editor found' }};
                }}

                // Set content
                targetEditor.setContent(arguments[0]);
                targetEditor.fire('change');
                targetEditor.fire('input');
                targetEditor.save();

                return {{
                    success: true,
                    method: 'tinyMCE.editors[] loop',
                    editorId: targetEditor.id
                }};
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        """, html_content)

        if result.get('success'):
            print(f"   ✅ SUCCESS via {result.get('method')} (Editor: {result.get('editorId')})")
            time.sleep(0.5)
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # ================================================================
    # 🔥 STRATEGY 4: Direct textarea + triggerSave
    # ================================================================
    print(f"\n🔥 Strategy 4: Direct textarea manipulation + triggerSave")
    try:
        result = driver.execute_script(f"""
            try {{
                var content = arguments[0];
                var htmlContent = arguments[1];
                var editorId = '{editor_id}';

                // 1. Set textarea value
                var textarea = document.getElementById(editorId);
                if (!textarea) {{
                    return {{ success: false, error: 'Textarea not found' }};
                }}

                textarea.value = content;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));

                // 2. Trigger TinyMCE to load from textarea
                if (typeof tinyMCE !== 'undefined') {{
                    var editor = tinyMCE.get(editorId);
                    if (editor) {{
                        // Load from textarea
                        editor.load();
                        // Or set directly
                        editor.setContent(htmlContent);
                        // Then save back
                        editor.save();
                        editor.fire('change');

                        return {{ success: true, method: 'textarea + editor.load/save' }};
                    }}
                }}

                return {{ success: true, method: 'textarea only' }};
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        """, content, html_content)

        if result.get('success'):
            print(f"   ✅ SUCCESS via {result.get('method')}")
            time.sleep(0.5)
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # ================================================================
    # 🔥 STRATEGY 5: Direct iframe body manipulation (Last Resort)
    # ================================================================
    print(f"\n🔥 Strategy 5: Direct iframe body manipulation (Last Resort)")

    # Multi-strategy tìm iframe với retry
    MAX_ATTEMPTS = 5
    iframe_element = None

    for attempt in range(MAX_ATTEMPTS):
        print(f"\n🔍 Attempt {attempt + 1}/{MAX_ATTEMPTS}: Tìm iframe...")

        if attempt > 0:
            wait_time = min(2 ** attempt, 8)  # Exponential backoff: 2, 4, 8s
            print(f"   ⏳ Retry delay: {wait_time}s...")
            time.sleep(wait_time)

            # Scroll lại để refresh
            driver.execute_script("window.scrollTo(0, 400);")
            time.sleep(0.5)

        # Debug: Count iframes
        try:
            all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"   📊 Total iframes on page: {len(all_iframes)}")

            # Log iframe IDs for debugging
            for idx, ifr in enumerate(all_iframes[:5]):  # Show first 5
                try:
                    ifr_id = ifr.get_attribute("id") or "no-id"
                    ifr_src = ifr.get_attribute("src") or "no-src"
                    print(f"      Iframe #{idx+1}: id='{ifr_id}', src='{ifr_src[:50]}...'")
                except:
                    pass
        except Exception as e:
            print(f"   ⚠️ Debug iframe count error: {e}")

        # STRATEGY 1: Tìm bằng ID chính xác
        try:
            print(f"   🎯 Strategy 1: Find by ID...")
            iframe_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, iframe_id))
            )
            if iframe_element and iframe_element.is_displayed():
                print(f"   ✅ Found by ID!")
                break
            else:
                print(f"   ⚠️ Found by ID but not visible")
                iframe_element = None
        except (TimeoutException, NoSuchElementException) as e:
            print(f"   ❌ Strategy 1 failed: {type(e).__name__}")
        except StaleElementReferenceException:
            print(f"   ⚠️ Stale element, retry...")
            iframe_element = None

        # STRATEGY 2: Tìm bằng XPath
        if not iframe_element:
            try:
                print(f"   🎯 Strategy 2: Find by XPath...")
                iframe_xpath = f"//*[@id='{iframe_id}']"
                iframe_element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, iframe_xpath))
                )
                if iframe_element and iframe_element.is_displayed():
                    print(f"   ✅ Found by XPath!")
                    break
                else:
                    iframe_element = None
            except Exception as e:
                print(f"   ❌ Strategy 2 failed: {type(e).__name__}")

        # STRATEGY 3: Tìm bằng CSS Selector
        if not iframe_element:
            try:
                print(f"   🎯 Strategy 3: Find by CSS selector...")
                css_selector = f"iframe#{iframe_id}"
                iframe_element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
                )
                if iframe_element and iframe_element.is_displayed():
                    print(f"   ✅ Found by CSS!")
                    break
                else:
                    iframe_element = None
            except Exception as e:
                print(f"   ❌ Strategy 3 failed: {type(e).__name__}")

        # STRATEGY 4: Scan all iframes chứa "tinymce"
        if not iframe_element:
            try:
                print(f"   🎯 Strategy 4: Scan all iframes for tinymce...")
                all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for idx, ifr in enumerate(all_iframes):
                    try:
                        ifr_id = ifr.get_attribute("id") or ""
                        if "tinymce" in ifr_id.lower() or policy_type.lower() in ifr_id.lower():
                            print(f"   ✅ Found matching iframe #{idx+1}: {ifr_id}")
                            iframe_element = ifr
                            break
                    except StaleElementReferenceException:
                        continue
                if iframe_element:
                    break
            except Exception as e:
                print(f"   ❌ Strategy 4 failed: {type(e).__name__}")

        # Nếu hết các strategy mà không tìm thấy
        if not iframe_element and attempt < MAX_ATTEMPTS - 1:
            print(f"   ⚠️ All strategies failed, will retry...")

    # Nếu sau tất cả attempts vẫn không tìm thấy
    if not iframe_element:
        print(f"❌ FAILED: Không tìm thấy iframe sau {MAX_ATTEMPTS} attempts!")
        return False

    # BƯỚC 3: Switch vào iframe với retry
    print(f"\n🔄 Switching to iframe...")
    switch_success = False
    for switch_attempt in range(3):
        try:
            driver.switch_to.frame(iframe_element)
            switch_success = True
            print(f"   ✅ Switched successfully")
            break
        except StaleElementReferenceException:
            print(f"   ⚠️ Stale iframe, refetch and retry {switch_attempt+1}/3...")
            time.sleep(1)
            try:
                # Refetch iframe
                iframe_element = driver.find_element(By.ID, iframe_id)
                driver.switch_to.frame(iframe_element)
                switch_success = True
                print(f"   ✅ Switched after refetch")
                break
            except:
                continue
        except Exception as e:
            print(f"   ❌ Switch error: {e}")
            time.sleep(1)

    if not switch_success:
        print(f"❌ FAILED: Không thể switch vào iframe!")
        return False

    # BƯỚC 4: Tìm body trong iframe
    print(f"\n🎯 Finding body in iframe...")
    body_element = None
    body_selectors = [
        "body"
    ]

    for selector in body_selectors:
        try:
            print(f"   🔍 Trying selector: {selector}")
            body_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if body_element:
                print(f"   ✅ Found body!")
                break
            else:
                body_element = None
        except Exception as e:
            print(f"   ❌ Selector failed: {type(e).__name__}")

    if not body_element:
        print(f"❌ FAILED: Không tìm thấy body!")
        driver.switch_to.default_content()
        return False

    # BƯỚC 5: Inject content với MULTIPLE methods
    print(f"\n💉 Injecting content into iframe body...")
    try:
        # Highlight để user thấy
        highlight_element(driver, body_element)
        time.sleep(0.3)

        # Method 1: innerHTML
        print(f"   📝 Method 1: innerHTML")
        driver.execute_script("arguments[0].innerHTML = arguments[1];", body_element, html_content)
        time.sleep(0.2)

        # Method 2: execCommand (for contenteditable)
        print(f"   📝 Method 2: execCommand")
        driver.execute_script("""
            var body = arguments[0];
            var content = arguments[1];

            // Select all content
            var range = document.createRange();
            range.selectNodeContents(body);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);

            // Delete existing content
            document.execCommand('delete', false, null);

            // Insert new content
            document.execCommand('insertHTML', false, content);
        """, body_element, html_content)
        time.sleep(0.2)

        # Method 3: Direct content manipulation
        print(f"   📝 Method 3: textContent then innerHTML")
        driver.execute_script("""
            var body = arguments[0];
            var content = arguments[1];

            // Clear first
            body.textContent = '';
            // Then set HTML
            body.innerHTML = content;
        """, body_element, html_content)
        time.sleep(0.2)

        # AGGRESSIVE event triggering
        driver.execute_script("""
            var body = arguments[0];

            // Focus first
            body.focus();

            // Trigger ALL relevant events
            var events = ['input', 'change', 'keydown', 'keyup', 'keypress', 'blur', 'focus', 'DOMSubtreeModified'];
            events.forEach(function(eventType) {
                var event;
                if (eventType.startsWith('key')) {
                    event = new KeyboardEvent(eventType, { bubbles: true, cancelable: true });
                } else {
                    event = new Event(eventType, { bubbles: true, cancelable: true });
                }
                body.dispatchEvent(event);
            });

            // Force blur then focus again
            body.blur();
            setTimeout(function() { body.focus(); }, 50);
        """, body_element)

        print(f"   ✅ Content injected via iframe body")

    except Exception as e:
        print(f"   ❌ Injection error: {e}")
        driver.switch_to.default_content()
        return False

    # BƯỚC 6: Switch back và sync với textarea + TinyMCE
    print(f"\n🔄 Switching back to main content...")
    driver.switch_to.default_content()
    time.sleep(0.3)

    # Sync với textarea VÀ trigger TinyMCE save
    try:
        print(f"   🔗 Final sync: textarea + TinyMCE triggerSave")
        result = driver.execute_script(f"""
            try {{
                var content = arguments[0];
                var htmlContent = arguments[1];
                var editorId = '{editor_id}';

                // 1. Update textarea directly
                var textarea = document.getElementById(editorId);
                if (textarea) {{
                    textarea.value = content;

                    // Trigger events on textarea
                    ['input', 'change', 'blur', 'focus'].forEach(function(eventType) {{
                        textarea.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
                    }});
                }}

                // 2. Trigger TinyMCE save/sync
                if (typeof tinyMCE !== 'undefined') {{
                    var editor = tinyMCE.get(editorId);
                    if (editor) {{
                        // Update editor content
                        editor.setContent(htmlContent);

                        // Trigger save (sync to textarea)
                        editor.save();

                        // Trigger change event
                        editor.fire('change');
                        editor.fire('NodeChange');

                        return {{ success: true, method: 'textarea + tinyMCE.save()' }};
                    }}
                }}

                // 3. Try with tinymce (lowercase)
                if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {{
                    tinymce.activeEditor.setContent(htmlContent);
                    tinymce.activeEditor.save();
                    tinymce.activeEditor.fire('change');
                    return {{ success: true, method: 'textarea + tinymce.save()' }};
                }}

                return {{ success: true, method: 'textarea only (TinyMCE not available)' }};
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        """, content, html_content)

        if result.get('success'):
            print(f"   ✅ Synced via: {result.get('method')}")
        else:
            print(f"   ⚠️ Sync warning: {result.get('error')}")

    except Exception as e:
        print(f"   ⚠️ Sync exception (might be OK): {e}")

    print(f"\n🎉 INJECTION COMPLETE via Strategy 5 (iframe fallback)!\n")
    return True

def _trigger_content_events(driver, element):
    """Trigger events cho contenteditable elements"""
    driver.execute_script("""
        var el = arguments[0];
        el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
        el.dispatchEvent(new Event('focus', { bubbles: true }));
    """, element)

def _trigger_textarea_events(driver, textarea):
    """Trigger events cho textarea elements"""
    driver.execute_script("""
        var ta = arguments[0];
        ta.dispatchEvent(new Event('input', { bubbles: true }));
        ta.dispatchEvent(new Event('change', { bubbles: true }));
        ta.dispatchEvent(new Event('blur', { bubbles: true }));
        ta.dispatchEvent(new Event('focus', { bubbles: true }));
        if (ta.form) {
            ta.form.dispatchEvent(new Event('input', { bubbles: true }));
            ta.form.dispatchEvent(new Event('change', { bubbles: true }));
        }
    """, textarea)

def _smart_click_save_button(driver: webdriver.Chrome, should_stop_callback=None, max_wait: int = 20) -> bool:
    """
    🎯 SMART BUTTON FINDER & CLICKER với multi-strategy

    Chiến lược:
    1. Tìm button bằng nhiều selector khác nhau
    2. Kiểm tra trạng thái enabled/disabled
    3. Scroll vào view nếu cần
    4. Retry với exponential backoff
    5. Force click bằng JavaScript nếu normal click fail

    Args:
        driver: WebDriver instance
        should_stop_callback: Callback để check user stop
        max_wait: Thời gian chờ tối đa (seconds)

    Returns:
        True nếu click thành công, False nếu fail
    """
    # Danh sách các selector để tìm button
    button_selectors = [
        # XPath - case insensitive
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'publish')]",
        "//button[@type='submit' and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]",
        # CSS Selector
        "button[type='submit']",
        # Aria label
        "//button[@aria-label='Save']",
        "//button[@aria-label='Publish']",
    ]

    start_time = time.time()
    attempt = 0
    last_error = None

    while time.time() - start_time < max_wait:
        # Check stop flag
        if should_stop_callback and should_stop_callback():
            print("\n⏹️ DỪNG TASK - User đã nhấn Stop button")
            return False

        attempt += 1
        if attempt == 1:
            print(f"   🔍 Searching for button...")
        elif attempt % 5 == 0:
            print(f"   ⏳ Still waiting... ({int(time.time() - start_time)}s)")

        # Thử từng selector
        for idx, selector in enumerate(button_selectors):
            try:
                # Xác định locator type
                if selector.startswith("//"):
                    locator = (By.XPATH, selector)
                else:
                    locator = (By.CSS_SELECTOR, selector)

                # Tìm button
                button = driver.find_element(*locator)

                if not button:
                    continue

                # Kiểm tra visibility
                if not button.is_displayed():
                    continue

                # Kiểm tra enabled/disabled
                is_enabled = button.is_enabled()
                aria_disabled = button.get_attribute("aria-disabled")
                is_clickable = is_enabled and (aria_disabled is None or aria_disabled == "false")

                if not is_clickable:
                    # Button tìm thấy nhưng chưa enabled, chờ thêm
                    if attempt == 1:
                        print(f"   ⏳ Button found but disabled, waiting...")
                    time.sleep(0.5)
                    continue

                # Button sẵn sàng click!
                print(f"   ✅ Button found and enabled (strategy #{idx+1})")

                # Scroll vào view
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        button
                    )
                    time.sleep(0.3)
                except:
                    pass

                # Highlight
                try:
                    highlight_element(driver, button)
                    time.sleep(0.2)
                except:
                    pass

                # CLICK với multiple strategies
                click_success = False

                # Strategy 1: Normal click
                try:
                    button.click()
                    click_success = True
                    print(f"   ✅ Clicked with .click()")
                except Exception as e1:
                    print(f"   ⚠️ Normal click failed: {type(e1).__name__}")

                # Strategy 2: JavaScript click
                if not click_success:
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        click_success = True
                        print(f"   ✅ Clicked with JavaScript")
                    except Exception as e2:
                        print(f"   ⚠️ JS click failed: {type(e2).__name__}")

                # Strategy 3: Action Chains click
                if not click_success:
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        ActionChains(driver).move_to_element(button).click().perform()
                        click_success = True
                        print(f"   ✅ Clicked with ActionChains")
                    except Exception as e3:
                        print(f"   ⚠️ ActionChains click failed: {type(e3).__name__}")

                if click_success:
                    time.sleep(1)  # Đợi sau khi click
                    return True
                else:
                    last_error = "All click strategies failed"

            except NoSuchElementException:
                # Selector này không tìm thấy, thử selector tiếp theo
                continue
            except StaleElementReferenceException:
                # Element bị stale, thử lại
                print(f"   ⚠️ Stale element, retrying...")
                time.sleep(0.5)
                break  # Break inner loop để retry từ đầu
            except Exception as e:
                # Lỗi khác
                last_error = str(e)
                continue

        # Đợi trước khi retry
        time.sleep(0.5)

    # Timeout
    print(f"   ❌ Button click timeout after {max_wait}s")
    if last_error:
        print(f"   Last error: {last_error}")
    return False

def setup_legal_policies(driver: webdriver.Chrome, storeId: str, policies: Dict[str, Any], should_stop_callback=None) -> None:
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
            # Check stop flag trước khi xử lý mỗi page
            if should_stop_callback and should_stop_callback():
                print("\n⏹️ DỪNG TASK - User đã nhấn Stop button")
                return
            print(f"\n📋 Đang xử lý: {page['name']}...")
            print(f"URL: {page['url']}")

            # Vào trang policy
            driver.get(page['url'])

            # Đợi page load - tăng timeout cho GUI threading
            print(f"⏳ Đang đợi page load...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print(f"✅ Page loaded")

            # Delay đặc biệt cho Shipping Policy (thường load chậm hơn)
            if page['name'] == "Shipping Policy":
                print(f"⏳ Shipping Policy thường load chậm, đợi thêm...")
                delay(5)  # Thêm 5s delay cho Shipping Policy
            else:
                # Đợi lâu hơn cho iframe load trong GUI threading environment
                print(f"⏳ Đang đợi iframe/editor load...")
                delay(3)

            # Debug: Check số lượng iframe
            iframe_count = len(driver.find_elements(By.TAG_NAME, "iframe"))
            print(f"🔍 DEBUG: Tìm thấy {iframe_count} iframe(s) trên page")

            # Scroll để trigger lazy-load
            driver.execute_script("window.scrollTo(0, 400);")
            delay(1)

            # Lấy nội dung policy từ GUI
            policy_content = policies.get(page['policy_key'], '').strip()
            if policy_content:
                print(f"📝 Đang nhập nội dung policy cho {page['name']}...")

                # Sử dụng SMART injection với multi-layered fallback
                # Map policy name to policy type
                policy_type_map = {
                    "Refund Policy": "REFUND_POLICY",
                    "Terms of Service": "TERMS_OF_SERVICE",
                    "Shipping Policy": "SHIPPING_POLICY",
                    "Contact Information": "CONTACT_INFORMATION"
                }
                policy_xpath_type = policy_type_map.get(page['name'], "TERMS_OF_SERVICE")

                success = inject_policy_content_smart(driver, policy_content, policy_xpath_type)

                if success:
                    print(f"✅ Đã nhập nội dung policy cho {page['name']}")
                else:
                    print(f"⚠️ Không thể nhập nội dung policy cho {page['name']}")
            else:
                print(f"⚠️ Không có nội dung policy cho {page['name']}")

            # 🎯 SMART BUTTON CLICK với multi-strategy
            print(f"\n� Tìm và click Save button...")
            button_clicked = _smart_click_save_button(driver, should_stop_callback)

            if button_clicked:
                print(f"   ✅ Button clicked successfully!")
            else:
                print(f"   ⚠️ Button click failed or timeout")

            # Delay ngắn giữa các pages
            delay(1)

        print("\n✅ HOÀN TẤT SETUP LEGAL POLICIES!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi setup legal policies: {e}")
        print("="*60)