import random
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ==========================================
# CẤU HÌNH
# ==========================================

# Nếu bạn dùng Google Sheets, chỉnh lại 3 dòng này:
USE_GOOGLE_SHEETS = True  # Đổi thành True nếu muốn lấy keyword từ Sheets
SPREADSHEET_ID = "1c8gCqUg7cPKJ9QiY977-4yQFJ93rl4cE4BscfPQhLP8"
SHEET_RANGE = "B2:B"

# Nếu không dùng Sheets thì dùng list local (demo 10 keyword)
LOCAL_KEYWORDS = [
    "YouTube", "Amazon", "Facebook", "Google", "Weather",
    "Gmail", "Wordle", "Google Translate", "Translate", "Walmart",
]

MAX_KEYWORDS = 10  # tương đương maxLoop = 10 trong JSON


# ==========================================
# HÀM LẤY KEYWORD
# ==========================================

def get_keywords():
    if not USE_GOOGLE_SHEETS:
        return LOCAL_KEYWORDS[:MAX_KEYWORDS]

    # --- LẤY TỪ GOOGLE SHEETS (OPTIONAL) ---
    import gspread
    from google.oauth2.service_account import Credentials

    # Bạn cần file JSON key service account, chỉnh path bên dưới
    SERVICE_ACCOUNT_FILE = "service_account.json"

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID)
    ws = sheet.sheet1  # hoặc dùng tên sheet = sheet.worksheet("Sheet1")

    values = ws.get(SHEET_RANGE)
    # values là list các hàng [[colB], [colB], ...]
    keywords = [row[0] for row in values if row]
    return keywords[:MAX_KEYWORDS]


# ==========================================
# HÀM SCROLL NGẪU NHIÊN (PORT TỪ JS TRONG FILE)
# ==========================================

def random_scroll(page, config):
    """
    Mô phỏng đoạn JS cuộn trang ngẫu nhiên trong workflow GoLess.
    config:
        {
            "scrollStepMin": int,
            "scrollStepMax": int,
            "pauseDurationMin": int,
            "pauseDurationMax": int,
            "scrollSpeedMin": int,
            "scrollSpeedMax": int,
            "totalScrollTimeMin": int,
            "totalScrollTimeMax": int,
            "pausesMin": int,
            "pausesMax": int
        }
    Tất cả đơn vị là milliseconds, giống JS gốc.
    """

    def get_random_int(a, b):
        return random.randint(a, b)

    total_time = get_random_int(config["totalScrollTimeMin"], config["totalScrollTimeMax"])
    pauses = get_random_int(config["pausesMin"], config["pausesMax"])

    start_time = time.time()
    pause_durations = [
        get_random_int(config["pauseDurationMin"], config["pauseDurationMax"])
        for _ in range(pauses)
    ]

    while True:
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms >= total_time:
            break

        step = get_random_int(config["scrollStepMin"], config["scrollStepMax"])

        # cuộn bằng JS cho mượt giống bản gốc
        page.evaluate(
            """(step) => {
                window.scrollBy({top: step, left: 0, behavior: 'smooth'});
            }""",
            step
        )

        delay = get_random_int(config["scrollSpeedMin"], config["scrollSpeedMax"])

        # 10% cơ hội pause dài (giống logic Math.random() < 0.1)
        if pause_durations and random.random() < 0.1:
            pause = pause_durations.pop(0)
            time.sleep(pause / 1000.0)
        else:
            time.sleep(delay / 1000.0)


# Config scroll 1 (bản dài ~ 96-100 giây) – lấy từ block "Cuộn xuống" đầu tiên
LONG_SCROLL_CONFIG = {
    "scrollStepMin": 100,
    "scrollStepMax": 120,
    "pauseDurationMin": 3000,
    "pauseDurationMax": 5000,
    "scrollSpeedMin": 300,
    "scrollSpeedMax": 500,
    "totalScrollTimeMin": 95999,
    "totalScrollTimeMax": 99999,
    "pausesMin": 10,
    "pausesMax": 15,
}

# Config scroll 2 (bản ngắn ~13-16 giây) – từ block "Cuộn xuống" thứ hai
SHORT_SCROLL_CONFIG = {
    "scrollStepMin": 100,
    "scrollStepMax": 120,
    "pauseDurationMin": 3000,
    "pauseDurationMax": 5000,
    "scrollSpeedMin": 300,
    "scrollSpeedMax": 500,
    "totalScrollTimeMin": 12999,
    "totalScrollTimeMax": 15999,
    "pausesMin": 2,
    "pausesMax": 3,
}


# ==========================================
# DELAY RANDOM – PORT TỪ JAVASCRIPT-CODE BLOCK
# ==========================================

def random_delay(min_ms, max_ms):
    value = random.randint(min_ms, max_ms)
    time.sleep(value / 1000.0)


# delay tương ứng với:
# golessSetVariable('timeout', getRandomInt(3456, 6789))
def delay_phase_1():
    random_delay(3456, 6789)


# golessSetVariable('timeout', getRandomInt(30000, 45999))
def delay_phase_2():
    random_delay(30000, 45999)


# golessSetVariable('timeout', getRandomInt(15999, 16999))
def delay_phase_3():
    random_delay(15999, 16999)


# ==========================================
# HÀM CLICK "MORE RESULTS" (2 selector trong JSON)
# ==========================================

def click_more_results(page):
    selectors = [
        'span.RVQdVd',                      # "More results" text
        'span.ExCKkf.z1asCe.rzyADb',        # icon button trong JSON
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            el.wait_for(state="visible", timeout=3000)
            el.click()
            return True
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue
    return False


# ==========================================
# NHẬN COOKIES (NHƯ SELENIUM)
# ==========================================

def accept_cookies(page):
    xpaths = [
        "//button[contains(., 'I agree')]",
        "//button[contains(., 'Agree')]",
        "//button[contains(., 'Chấp nhận')]",
        "//button[contains(., 'Tôi đồng ý')]",
    ]
    for xp in xpaths:
        try:
            btn = page.locator(f"xpath={xp}").first
            btn.wait_for(state="visible", timeout=1500)
            btn.click()
            time.sleep(random.uniform(0.5, 1.2))
            break
        except Exception:
            continue


# ==========================================
# FIND SEARCH BOX – THAM KHẢO LOGIC SELENIUM
# ==========================================

# ==========================================
# FIND SEARCH BOX – KHỚP ĐÚNG UI GOOGLE HIỆN TẠI
# ==========================================

# CSS selector cho cả homepage (textarea) và trang kết quả (input)
SEARCH_SELECTORS = [
    "textarea[name='q']",
    "input[name='q']",
    "textarea.gLFyf",
    "input.gLFyf",
    "input[type='search']",
]

# Fallback XPATH như Selenium
SEARCH_XPATHS = [
    "//textarea[@name='q']",
    "//input[@name='q']",
    "//textarea[contains(@class,'gLFyf')]",
    "//input[contains(@class,'gLFyf')]",
]

def click_search_container(page):
    containers = [
        "div.RNNXgb",                     # Google homepage main search box container
        "div.a4bIc",                      # inner container
        "div.gLFyf.gsfi"                  # sometimes clickable container
    ]
    for selector in containers:
        try:
            page.locator(selector).first.click(timeout=1000)
            return True
        except:
            pass
    return False

def find_search_box(page):

    # 1. CLICK SEARCH CONTAINER TRƯỚC CHO NÓ HIỆN TEXTAREA
    try:
        click_search_container(page)
        time.sleep(0.3)
    except:
        pass

    # 2. CSS selectors (UI Việt Nam dùng textarea.gLFyf)
    selectors = [
        "textarea.gLFyf",
        "textarea[name='q']",
        "input[name='q']",
        "input.gLFyf",
        "input[type='search']",
    ]

    for selector in selectors:
        try:
            el = page.locator(selector).first
            el.wait_for(state="attached", timeout=2000)
            el.wait_for(state="visible", timeout=2000)
            return el
        except:
            continue

    # 3. XPATH fallback
    xpaths = [
        "//textarea[contains(@class,'gLFyf')]",
        "//input[contains(@class,'gLFyf')]",
        "//textarea[@name='q']",
        "//input[@name='q']",
    ]

    for xp in xpaths:
        try:
            el = page.locator(f"xpath={xp}").first
            el.wait_for(state="visible", timeout=2000)
            return el
        except:
            continue

    return None

# ==========================================
# MAIN FLOW
# ==========================================

def run():
    keywords = get_keywords()
    print(f"Total keywords: {len(keywords)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200, channel='chrome', args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            locale="en-US",
        )
        context.add_init_script(
            """() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            }"""
        )

        page = context.new_page()

        for index, keyword in enumerate(keywords, start=1):
            print(f"[{index}] Searching: {keyword}")

            # Mở Google (block new-tab với URL https://www.google.com/)
            page.goto("https://www.google.com/", wait_until="domcontentloaded")

            # Nghỉ 1s giống delay 1000ms
            time.sleep(1)

            # Accept cookies nếu có
            accept_cookies(page)

            # Tìm ô search với logic mới
            search_box = find_search_box(page)
            if not search_box:
                print("❌ Không tìm thấy ô search, skip keyword này.")
                continue

            # Điền keyword (logic cũ: fill + Enter, không cần gõ từng ký tự)
            search_box.fill(keyword)
            search_box.press("Enter")

            # Chờ search results load
            page.wait_for_timeout(2000)

            # PHASE 1: delay ngắn + scroll dài
            delay_phase_1()
            print("  - Long scroll...")
            random_scroll(page, LONG_SCROLL_CONFIG)

            # PHASE 2: delay lớn + More results + scroll ngắn
            delay_phase_2()
            print("  - Trying to click 'More results'...")
            clicked = click_more_results(page)
            if clicked:
                print("    -> 'More results' clicked")
                page.wait_for_timeout(2000)
                print("  - Short scroll...")
                random_scroll(page, SHORT_SCROLL_CONFIG)
            else:
                print("    -> 'More results' not found, skipping short scroll")

            # PHASE 3: delay cuối trước khi qua keyword tiếp
            delay_phase_3()

        print("Done. Closing browser.")
        browser.close()


if __name__ == "__main__":
    run()
