from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element, click_save_button

def setup_selleasy(driver: webdriver.Chrome, storeId: str):
    print("\n" + "="*60)
    print("🚚 SETUP SELLEASY...")
    print("="*60)

    try:
        selleasy_url = f"https://admin.shopify.com/store/{storeId}/apps/lb-upsell"
        print(f"Đang vào trang: {selleasy_url}")
        driver.get(selleasy_url)

        # Đợi và chuyển vào iframe Selleasy
        print("Đang đợi iframe 'Selleasy' xuất hiện...")
        wait = WebDriverWait(driver, 15)
        iframe = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Selleasy']"))
        )
        print("Đã tìm thấy iframe, đang chuyển vào...")
        driver.switch_to.frame(iframe)
        delay(1)

        # Đợi và click button "Start free trial" đầu tiên
        print("Đang đợi nút 'Start free trial' đầu tiên xuất hiện...")
        start_trial_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[.//span[contains(text(), 'Start free trial')]]"))
        )
        print(f"Đã tìm thấy {len(start_trial_buttons)} nút 'Start free trial', đang click nút đầu tiên...")
        start_trial_buttons[0].click()
        print("✓ Đã click nút 'Start free trial' thành công")
        delay(2)

        # Đợi trang load và click button "Approve"
        print("Đang đợi nút 'Approve' xuất hiện...")
        approve_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Approve')]"))
        )
        print("Đã tìm thấy nút 'Approve', đang click...")
        approve_button.click()
        print("✓ Đã click nút 'Approve' thành công")
        delay(2)

        # Chuyển về nội dung chính
        driver.switch_to.default_content()

        print("✅ Đã hoàn thành setup Selleasy")

    except Exception as e:
        print(f"❌ Lỗi khi setup Selleasy: {e}")
        driver.switch_to.default_content()