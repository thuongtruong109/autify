import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from configs.driver import setup_driver


# ============================================================
# ------------- TÌM ELEMENT + CHỜ XUẤT HIỆN ------------------
# ============================================================

def find_h1_element(driver, text_to_find):
    """Tìm <h1> chứa text, trả về element hoặc None."""
    try:
        return driver.find_element(By.XPATH, f"//h1[contains(text(), '{text_to_find}')]")
    except:
        return None


def wait_until_h1_appears(driver, text_to_find, timeout=30, interval=0.3):
    """Poll liên tục cho đến khi H1 xuất hiện hoặc hết timeout."""
    print("⏳ Chờ H1 xuất hiện...")

    start = time.time()
    while time.time() - start < timeout:
        el = find_h1_element(driver, text_to_find)
        if el:
            print("🎉 H1 đã xuất hiện!")
            return el
        time.sleep(interval)
    print("⚠ H1 KHÔNG xuất hiện trong thời gian quy định!")
    return None


# ============================================================
# ------------------- TÔ VIỀN + CLICK ------------------------
# ============================================================

def highlight_element(driver, element, color="yellow"):
    """Tô viền element bằng JS."""
    driver.execute_script(f"arguments[0].style.outline='3px solid {color}';", element)


def click_offset_with_marker(driver, x, y):
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


# ============================================================
# -------------------- MAIN LOOP LOGIC -----------------------
# ============================================================

def click_h1_per_page_load(driver, text_to_find, offset_x=-180, offset_y=60,
                           random_clicks=6, random_range=25,
                           random_click_delay=(0.8, 1.5)):

    disappeared_count = 0  # đếm số lần không thấy element

    while True:
        print("\n🔎 BẮT ĐẦU MỘT LẦN KIỂM TRA MỚI 🔎")

        # Poll xem H1 có xuất hiện sau page load không
        element = wait_until_h1_appears(driver, text_to_find, timeout=20)

        # -------------------------------------------------------
        # Nếu element không xuất hiện → check tiếp nhiều lần
        # -------------------------------------------------------
        if not element:
            disappeared_count += 1
            print(f"⚠ Không thấy element (lượt {disappeared_count}/3)")

            if disappeared_count >= 3:
                print("✅ XÁC NHẬN element biến mất → DỪNG LOOP!")
                return

            print("🔄 Reload để kiểm tra lại...")
            driver.refresh()
            time.sleep(3)
            continue

        # Nếu thấy → reset counter
        disappeared_count = 0

        # -------------------------------------------------------
        # Tô viền vàng element
        # -------------------------------------------------------
        highlight_element(driver, element, "yellow")
        rect = element.rect
        base_x = rect['x'] + rect['width'] / 2
        base_y = rect['y'] + rect['height'] / 2
        print("✨ Element được tô viền vàng!")

        # -------------------------------------------------------
        # Random click × N lần
        # -------------------------------------------------------
        for _ in range(random_clicks):
            rand_x = base_x + random.randint(-random_range, random_range)
            rand_y = base_y + random.randint(-random_range, random_range)
            click_offset_with_marker(driver, rand_x, rand_y)
            print(f"🎯 Random click tại ({rand_x:.0f},{rand_y:.0f})")
            time.sleep(random.uniform(*random_click_delay))

        # -------------------------------------------------------
        # CLICK THẬT TẠI OFFSET
        # -------------------------------------------------------
        click_x = base_x + offset_x
        click_y = base_y + offset_y
        click_offset_with_marker(driver, click_x, click_y)
        print(f"🖱 CLICK THẬT tại ({click_x:.0f},{click_y:.0f})")

        # -------------------------------------------------------
        # RELOAD SAU CLICK THẬT
        # -------------------------------------------------------
        print("⏱ Đợi 7s rồi reload...")
        time.sleep(8)
        print("🔄 Reload page")
        driver.refresh()


# ============================================================
# -------------------- CHẠY TEST CHÍNH ------------------------
# ============================================================

def test_shopify_cloudflare_page_load_check():
    driver = setup_driver()
    driver.get("https://admin.shopify.com")

    time.sleep(5)

    text_to_click = "Your connection needs to be verified"

    click_h1_per_page_load(
        driver,
        text_to_click,
        offset_x=-180,
        offset_y=60,
        random_clicks=6,
        random_range=25,
        random_click_delay=(0.8, 1.5)
    )

    print("\nNhấn Enter để đóng browser...")
    input()
    driver.quit()


if __name__ == "__main__":
    test_shopify_cloudflare_page_load_check()
