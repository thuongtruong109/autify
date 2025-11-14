# safe_user_simulator.py
import random
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent

# --- Cấu hình ---
SEARCH_TERMS = [
    "python tutorial", "how to center div css", "weather today", "best coffee near me",
    "news technology", "learn selenium", "random trivia"
]  # danh sách tìm kiếm mẫu — thay bằng những từ bạn được phép dùng
RUN_DURATION_SECONDS = 5 * 60  # 5 minutes
MIN_ACTION_DELAY = 1.0
MAX_ACTION_DELAY = 4.0

# Chrome options (không dùng headless để tương tác giống người hơn)
ua = UserAgent()
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={ua.random}")
# options.add_argument("--start-maximized")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])  # optional

driver = webdriver.Chrome(options=options)  # hoặc webdriver.Chrome(executable_path="path/to/chromedriver", options=options)

def random_sleep(a=MIN_ACTION_DELAY, b=MAX_ACTION_DELAY):
    time.sleep(random.uniform(a, b))

def human_like_scroll(driver, total_seconds=20):
    """
    Cuộn trang theo chuyển động ngẫu nhiên trong khoảng total_seconds.
    """
    end_time = time.time() + total_seconds
    last_y = 0
    while time.time() < end_time:
        # chọn bước cuộn
        step = random.randint(100, 800)
        # đôi khi cuộn lên, đôi khi xuống để trông tự nhiên
        direction = random.choice([1, 1, 1, -1])  # ưu tiên cuộn xuống
        new_y = max(0, last_y + direction * step)
        driver.execute_script("window.scrollTo({left: 0, top: %d, behavior: 'smooth'});" % new_y)
        last_y = new_y
        random_sleep(0.4, 1.2)

def perform_search_and_browse(term):
    # Mở Google
    driver.get("https://www.google.com")
    random_sleep(1.0, 2.5)

    # chấp nhận cookies nếu pop-up (thử tìm button)
    try:
        # nút có thể có text "I agree", "Chấp nhận", "Tôi đồng ý", v.v. -> thử click nếu thấy
        for txt in ["I agree", "Agree", "Chấp nhận", "Tôi đồng ý"]:
            try:
                btn = driver.find_element(By.XPATH, f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{txt.lower()}')]")
                btn.click()
                random_sleep(0.5, 1.2)
                break
            except Exception:
                pass
    except Exception:
        pass

    # tìm ô search
    try:
        search_box = driver.find_element(By.NAME, "q")
    except Exception:
        # fallback: dùng xpath
        search_box = driver.find_element(By.XPATH, "//input[@type='text' or @name='q']")
    # nhập và submit
    search_box.clear()
    for ch in term:
        search_box.send_keys(ch)
        time.sleep(random.uniform(0.02, 0.12))  # gõ như người
    random_sleep(0.3, 0.8)
    search_box.send_keys(Keys.ENTER)

    # chờ kết quả load
    random_sleep(1.5, 3.0)

    # cuộn trang như người trong khoảng thời gian ngẫu nhiên (10-40s)
    human_like_scroll(driver, total_seconds=random.randint(10, 40))

    # đôi khi click link kết quả (chỉ click link có domain rõ ràng)
    try:
        results = driver.find_elements(By.XPATH, "//a[@href and .//h3]")
        if results:
            # chọn 0..2 links ngẫu nhiên
            clicks = random.choice([0, 0, 1])  # tăng chance không click
            for _ in range(clicks):
                elem = random.choice(results)
                try:
                    href = elem.get_attribute("href")
                    # chỉ click internal/simple links (bạn có thể bổ sung filter)
                    if href and href.startswith("http"):
                        elem.click()
                        random_sleep(2.0, 6.0)
                        # cuộn trang trong tab vừa mở
                        human_like_scroll(driver, total_seconds=random.randint(5, 20))
                        driver.back()
                        random_sleep(1.0, 3.0)
                except Exception:
                    pass
    except Exception:
        pass

# --- Main loop: chạy trong RUN_DURATION_SECONDS ---
start_time = datetime.now()
end_time = start_time + timedelta(seconds=RUN_DURATION_SECONDS)
print("Start simulation at", start_time.isoformat())

try:
    while datetime.now() < end_time:
        term = random.choice(SEARCH_TERMS)
        perform_search_and_browse(term)
        # nghỉ giữa các tìm kiếm (5-20s)
        random_sleep(5.0, 20.0)
finally:
    print("End simulation at", datetime.now().isoformat())
    driver.quit()
