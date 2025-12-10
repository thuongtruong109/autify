import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from configs.driver import setup_driver

def find_a_element(driver, text_to_find):
    try:
        return driver.find_element(By.XPATH, f"//a[contains(text(), '{text_to_find}')]")
    except:
        return None

def highlight_element(driver, element, color="yellow"):
    driver.execute_script(f"arguments[0].style.outline='3px solid {color}';", element)

def click_near_element(driver, element, x_offset, y_offset):
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(element, x_offset, y_offset).click().perform()
    actions.reset_actions()

    # Marker đỏ để quan sát
    rect = element.rect
    center_x = rect['width']/2 + x_offset
    center_y = rect['height']/2 + y_offset
    js_marker = f"""
    const marker = document.createElement('div');
    marker.style.position = 'absolute';
    marker.style.left = '{rect['x'] + center_x - 5}px';
    marker.style.top = '{rect['y'] + center_y - 5}px';
    marker.style.width = '10px';
    marker.style.height = '10px';
    marker.style.background='red';
    marker.style.borderRadius='50%';
    marker.style.zIndex='9999';
    document.body.appendChild(marker);
    """
    driver.execute_script(js_marker)

def click_a_per_page_load(driver, text_to_find,
                          offset_x=-150, offset_y=90,
                          random_clicks=6, random_range=(20,100),
                          random_click_delay=(0.8, 1.5)):
    while True:
        time.sleep(5)
        element = find_a_element(driver, text_to_find)
        if not element:
            print("✅ Element không còn xuất hiện, dừng loop!")
            break

        highlight_element(driver, element, "yellow")
        rect = element.rect
        width, height = rect['width'], rect['height']
        print(f"✅ Element xuất hiện, tô viền vàng!")

        for _ in range(random_clicks):
            dx = random.choice([-1,1]) * random.randint(width//2 + random_range[0],
                                                         width//2 + random_range[1])
            dy = random.choice([-1,1]) * random.randint(height//2 + random_range[0],
                                                         height//2 + random_range[1])
            click_near_element(driver, element, dx, dy)
            print(f"🎯 Random click gần element với offset ({dx},{dy})")
            time.sleep(random.uniform(*random_click_delay))

        click_near_element(driver, element, offset_x, offset_y)
        print(f"🖱 Click thật tại offset ({offset_x},{offset_y}) từ element")

        print("⏱ Đợi 5s trước khi reload page...")
        time.sleep(5)
        print("🔄 Reload page sau click thật")
        driver.refresh()

def test_shopify_cloudflare_page_load_check():
    driver = setup_driver()
    driver.get("https://2captcha.com/demo/cloudflare-turnstile")
    time.sleep(5)  # đợi page load ban đầu

    text_to_click = "Cloudflare Challenge"
    click_a_per_page_load(driver, text_to_click,
                          offset_x=-150, offset_y=90,
                          random_clicks=6,
                          random_range=(20,100),
                          random_click_delay=(0.8, 1.5))

    print("\nNhấn Enter để đóng browser...")
    input()
    driver.quit()

if __name__ == "__main__":
    test_shopify_cloudflare_page_load_check()
