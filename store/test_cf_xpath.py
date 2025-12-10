import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from configs.driver import setup_driver

def find_h1_element(driver, text_to_find):
    """Tìm <h1> chứa text, trả về element hoặc None."""
    try:
        return driver.find_element(By.XPATH, f"//h1[contains(text(), '{text_to_find}')]")
    except:
        return None

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

def click_h1_per_page_load(driver, text_to_find, offset_x=-180, offset_y=60,
                           random_clicks=6, random_range=25,
                           random_click_delay=(0.8, 1.5)):
    """
    Mỗi lần page load:
    - Check element
    - Nếu thấy → random click + click thật + reload
    - Lặp lại cho tới khi element biến mất
    """
    while True:
        # Chờ page load xong
        time.sleep(3)
        element = find_h1_element(driver, text_to_find)
        if not element:
            print("✅ Element không còn xuất hiện, dừng loop!")
            break

        highlight_element(driver, element, "yellow")
        rect = element.rect
        base_x = rect['x'] + rect['width']/2
        base_y = rect['y'] + rect['height']/2
        print(f"✅ Element xuất hiện, tô viền vàng!")

        # Random click nhiều lần
        for _ in range(random_clicks):
            rand_x = base_x + random.randint(-random_range, random_range)
            rand_y = base_y + random.randint(-random_range, random_range)
            click_offset_with_marker(driver, rand_x, rand_y)
            print(f"🎯 Random click tại ({rand_x:.0f},{rand_y:.0f}) với marker đỏ")
            time.sleep(random.uniform(*random_click_delay))

        # Click thật tại offset
        click_x = base_x + offset_x
        click_y = base_y + offset_y
        click_offset_with_marker(driver, click_x, click_y)
        print(f"🖱 Click thật tại ({click_x:.0f},{click_y:.0f}) với marker đỏ")

        # Đợi 5s rồi reload page
        print("⏱ Đợi 5s trước khi reload page...")
        time.sleep(7)
        print("🔄 Reload page sau click thật")
        driver.refresh()

def test_shopify_cloudflare_page_load_check():
    driver = setup_driver()
    driver.get("https://admin.shopify.com")
    time.sleep(5)  # đợi page load ban đầu

    text_to_click = "Your connection needs to be verified"
    click_h1_per_page_load(driver, text_to_click,
                            offset_x=-180, offset_y=60,
                            random_clicks=6,
                            random_range=25,
                            random_click_delay=(0.8, 1.5))

    print("\nNhấn Enter để đóng browser...")
    input()
    driver.quit()

if __name__ == "__main__":
    test_shopify_cloudflare_page_load_check()
