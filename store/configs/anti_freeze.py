import threading
import time
import traceback

class AntiFreeze:
    def __init__(self, driver, interval=15):
        self.driver = driver
        self.interval = interval
        self.running = False
        self.thread = None

    def _keep_alive(self):
        while self.running:
            try:
                self.driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
            except Exception:
                traceback.print_exc()
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
