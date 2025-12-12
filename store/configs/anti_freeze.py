import threading
import time

class AntiFreeze:
    def __init__(self, driver, interval=15):
        self.driver = driver
        self.interval = interval
        self.running = False
        self.thread = None

    def _keep_alive(self):
        consecutive_errors = 0
        max_errors = 3

        while self.running:
            try:
                if self.driver:
                    self.driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
                    consecutive_errors = 0
                else:
                    print("⚠️ AntiFreeze: Driver không còn khả dụng, dừng heartbeat")
                    break
            except Exception as e:
                consecutive_errors += 1
                error_msg = str(e).lower()

                if "invalid session" in error_msg or "chrome not reachable" in error_msg:
                    print(f"⚠️ AntiFreeze: Driver lost connection, dừng heartbeat")
                    break

                if consecutive_errors >= max_errors:
                    print(f"⚠️ AntiFreeze: Quá nhiều lỗi ({max_errors}), dừng heartbeat")
                    break

            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(
                target=self._keep_alive,
                daemon=True
            )
            self.thread.start()
            print("Anti-Freeze heartbeat started.")

    def stop(self):
        self.running = False
        print("Anti-Freeze stopped.")
