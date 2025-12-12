# Threading Architecture - Autify Store Automation

## 📐 Kiến trúc 3 Threads độc lập

Hệ thống đã được refactor để chạy trên 3 threads hoàn toàn độc lập, tránh xung đột và blocking:

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN APPLICATION                         │
│                                                             │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  GUI Thread    │  │  Selenium    │  │   Captcha      │ │
│  │   (Main)       │  │   Thread     │  │   Thread       │ │
│  └────────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1️⃣ GUI Thread (Main Thread)

**Vai trò:** Xử lý tất cả UI operations và user interactions

**Responsibilities:**

- Render giao diện người dùng (Tkinter/PySide6)
- Xử lý events: click, input, hover, etc.
- Update widgets: labels, textboxes, buttons, progress bars
- Không bao giờ chạy blocking operations

**Luồng hoạt động:**

```python
# User click Login button → GUI thread
def login_action(self):
    # Validate input (non-blocking)
    if not self.validate_login_inputs():
        return

    # Disable UI elements
    self.login_button.setEnabled(False)

    # Send signal đến Selenium thread (non-blocking)
    self.signals.do_login.emit(email, password, store_id)

    # GUI thread KHÔNG BỊ BLOCK - tiếp tục xử lý events
```

**Key Points:**

- ✅ Không bao giờ gọi Selenium commands trực tiếp
- ✅ Communicate với Selenium thread qua Signals/Slots
- ✅ Update UI qua signals từ worker threads
- ✅ Always responsive, không bị đơ

---

### 2️⃣ Selenium Thread (Worker Thread)

**Vai trò:** Chạy tất cả Selenium operations (browser automation)

**Responsibilities:**

- Initialize và quản lý WebDriver
- Thực hiện login, navigation, form filling
- Execute các tasks: install apps, setup policies, etc.
- Quản lý AntiFreeze heartbeat

**Class:** `SeleniumWorker(QObject)`

- Được move vào QThread riêng
- Nhận commands từ GUI thread qua signals
- Emit signals để update GUI

**Communication Pattern:**

```python
# GUI Thread → Selenium Thread
self.signals.do_login.emit(email, password, store_id)

# Selenium Thread → GUI Thread
self.gui.signals.log_message.emit("Login successful!")
self.gui.signals.login_success.emit()
```

**Workflow Example (Login):**

```python
@Slot(str, str, str)
def perform_login(self, email, password, store_id):
    """Chạy trong Selenium thread - KHÔNG block GUI"""

    # Setup driver nếu chưa có
    if not self.driver:
        self.driver = self.setup_driver_and_heartbeat()

    # Thực hiện login (blocking operation - nhưng trong thread riêng)
    logged = login_to_shopify(self.driver, email, password, store_id)

    # Emit signal về GUI thread
    if logged:
        self.gui.signals.login_success.emit()
    else:
        self.gui.signals.login_failed.emit("Login failed")
```

**Key Points:**

- ✅ Chạy trong thread riêng, không block GUI
- ✅ Tất cả Selenium operations ở đây
- ✅ Captcha monitor tự động can thiệp khi cần
- ✅ Communicate với GUI qua signals (thread-safe)

---

### 3️⃣ Captcha Thread (Background Monitor)

**Vai trò:** Tự động detect và xử lý captcha

**Responsibilities:**

- Liên tục monitor browser mỗi 2 giây
- Detect Cloudflare và Shopify captcha
- Tự động solve captcha khi phát hiện
- Không cần explicit calls từ main logic

**Architecture:**

```python
# Thread này chạy độc lập, không cần gọi từ code
start_captcha_monitor(driver, check_interval=2.0)

# Background loop (chạy trong thread riêng)
while _captcha_monitor_active:
    # Check captcha (silent)
    if captcha_detected:
        # Lock để tránh xử lý trùng
        with _captcha_lock:
            # Can thiệp vào driver để solve captcha
            cloudflare_captcha(driver, verbose=True)

    time.sleep(check_interval)
```

**Interaction với Selenium Thread:**

```
Selenium Thread                    Captcha Thread
      |                                 |
      ├─ navigate(url)                  ├─ (check...) ✓ OK
      ├─ fill_email()                   ├─ (check...) ✓ OK
      ├─ click_button()                 ├─ (check...) ⚠️ CAPTCHA!
      |                                 ├─ 🔒 LOCK + solve
      ├─ fill_password() ⏸️              |    (blocking monitor only)
      |    (đợi driver available)       ├─ solving...
      |    (tự động - không code gì)    ├─ solved! ✓
      ├─ ▶️ tiếp tục                     ├─ 🔓 UNLOCK
      └─ ...                            └─ (check...) ✓ OK
```

**Key Points:**

- ✅ **HOÀN TOÀN TỰ ĐỘNG** - không cần gọi wait/check
- ✅ Main logic viết như không có captcha
- ✅ Chạy trong thread riêng với own lock
- ✅ Can thiệp vào driver khi cần (thread-safe với Selenium)

---

## 🔄 Flow Diagram: Complete User Action

```
┌──────────────┐
│ User clicks  │
│ "Run Tasks"  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  GUI Thread (Main)                   │
│  • Validate inputs                   │
│  • Disable buttons                   │
│  • Emit signal: do_run_tasks()       │
└──────┬───────────────────────────────┘
       │ (Signal)
       ▼
┌──────────────────────────────────────┐
│  Selenium Thread (Worker)            │
│  • Receive signal via Slot           │
│  • Setup driver if needed            │
│  • Execute tasks sequentially        │
│  │                                   │
│  ├─ Task 1: install_apps()           │
│  │   ├─ Navigate to apps page        │──┐
│  │   ├─ Click install button         │  │
│  │   └─ Wait for confirmation        │  │
│  │                                   │  │
│  └─ Task 2: setup_policies()         │  │
│      ├─ Navigate to policies         │  │
│      ├─ Fill form fields             │  │
│      └─ Save                         │  │
│                                      │  │
│  • Emit log messages                 │  │
│  • Emit task_completed               │  │
└──────┬───────────────────────────────┘  │
       │ (Signal)                          │
       ▼                                   │
┌──────────────────────────────────────┐  │
│  GUI Thread (Main)                   │  │
│  • Receive task_completed            │  │
│  • Update UI: re-enable buttons      │  │
│  • Show success message              │  │
└──────────────────────────────────────┘  │
                                           │
    ┌──────────────────────────────────────┘
    │ (Meanwhile, parallel to Selenium)
    ▼
┌──────────────────────────────────────┐
│  Captcha Thread (Background)         │
│  • Continuously monitor every 2s     │
│  • If captcha detected:              │
│    ├─ Acquire lock                   │
│    ├─ Solve captcha                  │
│    ├─ Release lock                   │
│    └─ Continue monitoring            │
│  • Selenium thread pauses if needed  │
│    (automatic - no code changes)     │
└──────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### Signal/Slot Communication

**Định nghĩa Signals:**

```python
class WorkerSignals(QObject):
    # GUI → Selenium
    do_login = Signal(str, str, str)
    do_run_tasks = Signal(set, list, dict, dict, str)

    # Selenium → GUI
    log_message = Signal(str)
    login_success = Signal()
    login_failed = Signal(str)
    task_completed = Signal()
    task_error = Signal(str)
```

**Kết nối Slots:**

```python
class SeleniumWorker(QObject):
    def __init__(self, parent_gui):
        super().__init__()
        self.gui = parent_gui

        # Connect incoming signals
        self.gui.signals.do_login.connect(self.perform_login)
        self.gui.signals.do_run_tasks.connect(self.run_tasks)

    @Slot(str, str, str)
    def perform_login(self, email, password, store_id):
        # Implementation...
```

**Thread Setup:**

```python
def create_selenium_worker(self):
    """Tạo worker và thread"""
    self.selenium_thread = QThread()
    self.selenium_worker = SeleniumWorker(self)
    self.selenium_worker.moveToThread(self.selenium_thread)
    self.selenium_thread.start()
```

---

## 📊 Benefits của Architecture mới

### Before (Single Thread):

```
❌ GUI bị block khi Selenium chạy
❌ App có thể đơ/không phản hồi
❌ Browser có thể throttle khi background
❌ User không thể cancel operations
❌ Poor user experience
```

### After (3 Separate Threads):

```
✅ GUI luôn responsive
✅ Browser hoạt động tốt ở foreground
✅ Captcha được xử lý tự động song song
✅ User có thể cancel/interact bất cứ lúc nào
✅ Professional user experience
✅ Không xung đột giữa operations
```

---

## 🚀 Usage Examples

### Login Flow:

```python
# GUI Thread - User clicks Login
def login_action(self):
    credentials = self.get_credentials_from_inputs()

    # Create worker if not exists
    if not self.selenium_worker:
        self.create_selenium_worker()

    # Send to Selenium thread (non-blocking)
    self.signals.do_login.emit(
        credentials['email'],
        credentials['password'],
        credentials['storeId']
    )
    # GUI continues running immediately

# Selenium Thread - Performs login
@Slot(str, str, str)
def perform_login(self, email, password, store_id):
    if not self.driver:
        self.driver = self.setup_driver_and_heartbeat()

    # Blocking operation - but in separate thread
    logged = login_to_shopify(self.driver, email, password, store_id)

    # Notify GUI
    if logged:
        self.gui.signals.login_success.emit()
```

### Task Execution Flow:

```python
# GUI Thread - User clicks Run
def run_selected_tasks(self):
    # Prepare data
    credentials = self.get_credentials_from_inputs()

    # Send to Selenium thread
    self.signals.do_run_tasks.emit(
        self.selected_tasks.copy(),
        self.task_order.copy(),
        self.task_data.copy(),
        credentials,
        self.store_id
    )
    # GUI remains responsive

# Selenium Thread - Executes tasks
@Slot(set, list, dict, dict, str)
def run_tasks(self, selected_tasks, task_order, task_data, credentials, store_id):
    for task_id in sorted_tasks:
        if self.gui.should_stop_tasks:
            break

        task_func = task_data[task_id]['func']

        # Execute (blocking in this thread only)
        self.execute_single_task(task_func, ...)

        # Update GUI
        self.gui.signals.log_message.emit(f"✅ Completed: {task_label}")

    # Notify completion
    self.gui.signals.task_completed.emit()
```

---

## 🎯 Key Takeaways

1. **GUI Thread**: UI only - không chạy Selenium
2. **Selenium Thread**: Tất cả automation logic
3. **Captcha Thread**: Auto-monitor và solve (độc lập)
4. **Communication**: Chỉ qua Signals/Slots (thread-safe)
5. **Captcha Monitor**: Không cần thay đổi logic - vẫn can thiệp tự động

---

## 🔍 Troubleshooting

### GUI bị đơ?

- ❌ Kiểm tra xem có Selenium command nào chạy trong GUI thread không
- ✅ Đảm bảo tất cả blocking operations trong Selenium thread

### Captcha không được solve?

- ❌ Kiểm tra `start_captcha_monitor()` đã được gọi chưa
- ✅ Monitor tự động chạy khi setup driver

### Thread không communicate?

- ❌ Check signal/slot connections
- ✅ Ensure worker đã được moveToThread() trước khi start()

---

**Last Updated:** December 12, 2025
**Architecture Version:** 3.0 - Three Independent Threads
