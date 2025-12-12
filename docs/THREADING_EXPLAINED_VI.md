# Giải thích Threading Architecture - Autify

## 🎯 Vấn đề cần giải quyết

**Trước đây:**

- GUI và Selenium chạy cùng main thread
- Khi Selenium load trang/điền form → GUI bị đơ
- Browser có thể bị throttle khi chạy background
- Terminal chạy OK nhưng GUI .exe không thấy element

**Nguyên nhân:**

```
Main Thread (GUI)
    ├─ mainloop()  <--- Xử lý UI events
    └─ Selenium    <--- BLOCK ở đây → GUI đơ!
```

---

## ✅ Giải pháp: 3 Threads độc lập

```
┌─────────────────────────────────────────────────┐
│              APPLICATION                        │
│                                                 │
│   Thread 1          Thread 2         Thread 3  │
│  ┌─────────┐     ┌──────────┐    ┌──────────┐ │
│  │   GUI   │     │ Selenium │    │ Captcha  │ │
│  │ (Main)  │     │ (Worker) │    │ (Monitor)│ │
│  └─────────┘     └──────────┘    └──────────┘ │
│       ↑               ↑                ↑       │
│       │  Signals/     │                │       │
│       │  Slots        │    Auto-solve  │       │
│       └───────────────┘                │       │
│                                         │       │
└─────────────────────────────────────────────────┘
```

---

## 📝 Chi tiết từng Thread

### Thread 1: GUI (Main Thread)

**Chức năng:**

- Render giao diện
- Xử lý click, input, hover
- Update labels, buttons, progress bars

**Ví dụ:**

```python
def login_action(self):
    # Validate input
    if not self.validate_login_inputs():
        return

    # Disable button
    self.login_button.setEnabled(False)

    # GỬI SIGNAL đến Selenium thread (không block)
    self.signals.do_login.emit(email, password, store_id)

    # ← GUI thread TRẢ QUYỀN ĐIỀU KHIỂN NGAY
    # User vẫn có thể click, scroll, etc.
```

**Key:** GUI thread KHÔNG BAO GIỜ chạy Selenium commands!

---

### Thread 2: Selenium (Worker Thread)

**Chức năng:**

- Setup WebDriver
- Thực hiện login, navigation, tasks
- Gọi các hàm automation (install_apps, setup_policies...)

**Class:** `SeleniumWorker`

```python
class SeleniumWorker(QObject):
    """Chạy trong thread riêng"""

    @Slot(str, str, str)
    def perform_login(self, email, password, store_id):
        # NHẬN signal từ GUI thread

        # Setup driver (chỉ chạy 1 lần)
        if not self.driver:
            self.driver = self.setup_driver_and_heartbeat()

        # Login (blocking - nhưng ở thread riêng nên không sao)
        logged = login_to_shopify(self.driver, email, password, store_id)

        # GỬI KẾT QUẢ về GUI thread
        if logged:
            self.gui.signals.login_success.emit()
```

**Communication:**

```
GUI Thread  ──(signal: do_login)──>  Selenium Thread
                                           │
                                       (thực hiện)
                                           │
GUI Thread  <─(signal: login_success)── Selenium Thread
```

---

### Thread 3: Captcha (Background Monitor)

**Chức năng:**

- Tự động detect captcha mỗi 2 giây
- Tự động solve khi phát hiện
- KHÔNG CẦN gọi từ code

**Cách hoạt động:**

```python
# Được start khi setup driver
start_captcha_monitor(driver, check_interval=2.0)

# Chạy background loop trong thread riêng
while active:
    if detect_captcha():
        # Can thiệp vào driver
        solve_captcha()

    sleep(2)
```

**Tương tác với Selenium:**

```
Selenium Thread              Captcha Thread
     │                            │
     ├─ navigate()                ├─ check... ✓
     ├─ fill_email()              ├─ check... ✓
     ├─ click_submit()            ├─ check... ⚠️ CAPTCHA!
     │                            ├─ 🔒 LOCK
     │                            ├─ solving...
     ├─ (đợi...)  ⏸️               │
     │                            ├─ solved! ✓
     │                            └─ 🔓 UNLOCK
     ├─ tiếp tục ▶️
```

**Quan trọng:**

- Selenium thread KHÔNG CẦN đợi hay check captcha
- Viết code như không có captcha
- Monitor tự động xử lý trong nền

---

## 🔄 Flow hoàn chỉnh: User click "Run Tasks"

```
1. GUI Thread
   ┌────────────────────────────────┐
   │ User click "Run Tasks"         │
   │ • Validate inputs              │
   │ • Disable buttons              │
   │ • emit(do_run_tasks)           │ ─┐
   └────────────────────────────────┘  │
            ↓ Signal                    │
                                        │
2. Selenium Thread                     │
   ┌────────────────────────────────┐  │
   │ @Slot: run_tasks()             │  │
   │ • Setup driver                 │  │
   │ • Loop through tasks:          │  │
   │   ├─ Task 1: install_apps()    │  │
   │   ├─ Task 2: setup_policies()  │  │
   │   └─ Task 3: ...               │  │
   │ • emit(task_completed)         │ ─┤
   └────────────────────────────────┘  │
            ↓ Signal                    │
                                        │
3. GUI Thread                          │
   ┌────────────────────────────────┐  │
   │ @Slot: after_run_tasks()       │  │
   │ • Re-enable buttons            │  │
   │ • Show completion message      │  │
   └────────────────────────────────┘  │
                                        │
4. Captcha Thread (song song)          │
   ┌────────────────────────────────┐  │
   │ while True:                    │ ←┘
   │   check_captcha()              │ (chạy song song)
   │   if found: solve_captcha()    │
   │   sleep(2)                     │
   └────────────────────────────────┘
```

---

## 💡 Những điểm quan trọng cần nhớ

### 1. MỐI QUAN HỆ giữa Main Logic và Captcha

```
✅ GIỮ NGUYÊN - KHÔNG THAY ĐỔI
- Captcha monitor vẫn can thiệp khi cần
- Main logic không cần gọi wait/check
- Tự động như cũ, chỉ tách thread
```

### 2. Communication qua Signals/Slots

```python
# GUI → Selenium: emit signal
self.signals.do_login.emit(email, password, store_id)

# Selenium → GUI: emit signal
self.gui.signals.log_message.emit("Login successful!")
```

### 3. Không dùng threading.Thread trực tiếp

```python
# ❌ Cách cũ - blocking GUI
thread = threading.Thread(target=self.selenium_task)
thread.start()

# ✅ Cách mới - QThread + Worker
self.selenium_worker = SeleniumWorker(self)
self.selenium_worker.moveToThread(self.selenium_thread)
self.signals.do_task.emit(...)  # Non-blocking
```

---

## 📊 So sánh Before/After

### Before (1 Thread):

```
GUI + Selenium cùng Main Thread
    ↓
Selenium chạy → GUI đơ
    ↓
Browser background → Throttle
    ↓
Không tìm thấy element
```

### After (3 Threads):

```
GUI ────→ (Thread 1) Luôn responsive
Selenium ─→ (Thread 2) Chạy độc lập
Captcha ──→ (Thread 3) Auto-monitor

✅ Không block lẫn nhau
✅ Browser foreground
✅ Element luôn visible
✅ UX professional
```

---

## 🚀 Kết quả

- ✅ GUI không bao giờ bị đơ
- ✅ Selenium chạy mượt mà
- ✅ Captcha tự động xử lý
- ✅ Code dễ maintain
- ✅ User experience tốt

---

**Tóm lại:**
Tách thành 3 threads độc lập, communicate qua signals. Captcha monitor vẫn hoạt động như cũ trong thread riêng của nó.
