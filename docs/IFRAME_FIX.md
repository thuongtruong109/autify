# Quick Fix: TinyMCE Iframe Issue trong GUI Threading

## 🐛 Vấn đề

Sau khi refactor sang 3-thread architecture, chỉ có policy đầu tiên (Return & Refund) tìm thấy iframe, các policy sau không tìm thấy TinyMCE editor.

**Log lỗi:**
```
Đang nhập nội dung policy cho Terms of Service...
📝 Đang inject content...
🔍 Đang tìm iframe chứa element: body#tinymce[contenteditable='true']...
   Tìm thấy 0 iframe(s) trong trang.
⚠️ Không tìm thấy element 'body#tinymce[contenteditable='true']' trong bất kỳ iframe nào.
   ❌ Không tìm thấy input field.
⚠️ Không thể nhập nội dung policy cho Terms of Service
```

## 🔍 Nguyên nhân

Trong GUI threading environment, timing của việc load iframe có thể chậm hơn so với terminal mode vì:

1. **Browser rendering khác biệt**: Khi chạy từ GUI app, browser có thể render khác so với terminal
2. **Thread switching overhead**: Context switching giữa GUI thread và Selenium thread có thể gây delay nhỏ
3. **Page load timing**: Shopify có thể load iframe động sau khi page ready, cần thêm thời gian chờ

## ✅ Giải pháp đã implement

### 1. Tăng timeout và thêm delay

**File: `policies.py`**
```python
# Before
WebDriverWait(driver, 15).until(...)
delay(2)

# After
WebDriverWait(driver, 20).until(...)  # +5s timeout
delay(3)  # +1s delay cho iframe load

# Thêm debug logging
iframe_count = len(driver.find_elements(By.TAG_NAME, "iframe"))
print(f"🔍 DEBUG: Tìm thấy {iframe_count} iframe(s) trên page")

# Scroll để trigger lazy-load iframe
driver.execute_script("window.scrollTo(0, 400);")
delay(1)
```

### 2. Improved `find_iframe_with_selector()`

**File: `utils/element.py`**

**Thay đổi chính:**

```python
def find_iframe_with_selector(
    driver: webdriver.Chrome, 
    css_selector: str, 
    by: By = By.CSS_SELECTOR, 
    timeout: int = 10,
    max_retries: int = 3  # ← NEW: Retry logic
):
```

**Features mới:**

1. **Retry mechanism**: Tự động retry 3 lần nếu không tìm thấy iframe
2. **Scroll before check**: Scroll xuống để trigger lazy-load
3. **Longer wait giữa retries**: 2 giây giữa mỗi lần retry
4. **Verify element visibility**: Check `element.is_displayed()` trước khi return
5. **Better error recovery**: Try-catch cho từng iframe riêng biệt

```python
# Retry loop
for retry in range(max_retries):
    if retry > 0:
        print(f"   🔄 Retry #{retry + 1}/{max_retries}...")
        time.sleep(2)  # Wait longer
    else:
        time.sleep(2)  # Initial wait
    
    # Scroll để trigger lazy-load
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(0.5)
    
    # Get iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    
    if len(iframes) == 0 and retry < max_retries - 1:
        print(f"   ⚠️ Chưa có iframe nào, retry...")
        continue
    
    # Check each iframe
    for idx, iframe in enumerate(iframes):
        # Skip invisible iframes
        if not iframe.is_displayed():
            continue
        
        # ... tìm element ...
        
        # Verify element visible
        if element.is_displayed():
            return element
```

### 3. Retry logic trong `inject_tinymce_content()`

**File: `policies.py`**

```python
def inject_tinymce_content(
    driver: webdriver.Chrome, 
    content: str, 
    max_retries: int = 3  # ← NEW parameter
) -> bool:
    
    # Retry loop cho việc tìm TinyMCE
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"   🔄 Attempt {attempt + 1}/{max_retries}...")
            driver.execute_script("window.scrollTo(0, 300);")
            delay(2)
        
        tinymce_body = find_iframe_with_selector(
            driver,
            "body#tinymce[contenteditable='true']",
            By.CSS_SELECTOR,
            timeout=10,
            max_retries=1
        )
        
        if tinymce_body:
            break  # Found!
        
        if attempt < max_retries - 1:
            print(f"   ⚠️ Không tìm thấy TinyMCE, retry...")
```

## 🧪 Testing

Để test các thay đổi:

1. **Run GUI app**:
```bash
cd "c:/Users/admin/Downloads/Personal/autify/store"
python gui.py
```

2. **Monitor logs** để xem:
   - Số lượng iframe detected
   - Retry attempts
   - Timing của việc load

3. **Check từng policy page**:
   - Return & Refund ✅ (đã work)
   - Terms of Service ← Cần check
   - Shipping Policy ← Cần check
   - Contact Information ← Cần check

## 📊 Expected Results

**Before fix:**
```
Policy 1: ✅ Found 1 iframe
Policy 2: ❌ Found 0 iframe
Policy 3: ❌ Found 0 iframe
Policy 4: ❌ Found 0 iframe
```

**After fix:**
```
Policy 1: ✅ Found 1 iframe (no retry needed)
Policy 2: ✅ Found 1 iframe (after 1-2 retries)
Policy 3: ✅ Found 1 iframe (after 1-2 retries)
Policy 4: ✅ Found 1 iframe (after 1-2 retries)
```

## 🔧 Nếu vẫn không work

### Debug Steps:

1. **Check timing**:
```python
# Trong setup_legal_policies(), sau driver.get(url):
print(f"⏳ Waiting 5s...")
delay(5)  # Force wait
```

2. **Check page state**:
```python
# Kiểm tra page đã load hết chưa
print(f"Ready state: {driver.execute_script('return document.readyState')}")
print(f"Iframe count: {len(driver.find_elements(By.TAG_NAME, 'iframe'))}")

# Wait thêm nếu iframe = 0
while len(driver.find_elements(By.TAG_NAME, "iframe")) == 0:
    print("Waiting for iframe...")
    delay(1)
```

3. **Check element trong main content** (không phải iframe):
```python
# Có thể Shopify đã thay đổi UI, không dùng iframe nữa
textareas = driver.find_elements(By.TAG_NAME, "textarea")
print(f"Found {len(textareas)} textarea(s)")

contentEditables = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
print(f"Found {len(contentEditables)} contenteditable element(s)")
```

## 💡 Root Cause Analysis

Vấn đề có thể xảy ra vì:

1. **Shopify dynamic loading**: Iframe được load sau khi page "complete"
2. **React/SPA behavior**: Shopify dùng React, content load async
3. **Threading timing**: Small delays accumulate trong multi-thread environment

**Solution**: Tăng wait times và thêm retry logic để accommodate timing differences.

## 📝 Next Steps

1. ✅ Test với các improvements hiện tại
2. ❓ Nếu vẫn fail, thêm debug logging như trên
3. ❓ Có thể cần fallback strategy (direct textarea injection)
4. ❓ Consider thêm explicit wait cho iframe element:

```python
# Wait cho iframe xuất hiện trước khi search
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.TAG_NAME, "iframe"))
)
print("✅ Iframe detected, searching for TinyMCE...")
```

---

**Status**: Improvements deployed, awaiting test results
**Date**: December 12, 2025
