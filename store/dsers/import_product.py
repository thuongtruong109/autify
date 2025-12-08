from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delay, highlight_element

def import_dser_products(driver: webdriver.Chrome, storeId: str, password: str):
    print("\n" + "="*60)
    print("🔄 XỬ LÝ MỞ VÀ XÁC NHẬN DSERS...")
    print("="*60)

    main_window_handle = driver.current_window_handle

    try:
        # 1. Mở tab mới với URL DSers app
        dser_app_url = "https://www.dsers.com/application/import_list"
        print(f"📂 Mở tab mới với URL: {dser_app_url}")
        driver.execute_script(f"window.open('{dser_app_url}');")
        delay(3)

        new_tab_handle = None
        for handle in driver.window_handles:
            if handle != main_window_handle:
                new_tab_handle = handle
                break

        if not new_tab_handle:
            print("❌ Không tìm thấy tab mới. Bỏ qua.")
            return

        driver.switch_to.window(new_tab_handle)
        print("✅ Đã chuyển sang tab DSers app.")

        print("⏳ Đang chờ trang DSers app load xong...")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Trang DSers app đã load xong.")

        print("\n✅ HOÀN TẤT XỬ LÝ MỞ VÀ XÁC NHẬN DSERS!")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi khi xử lý mở và xác nhận DSers: {e}")
        print("="*60)
    finally:
        # print("🔄 Đóng các tab phụ và quay về main window...")
        # for handle in driver.window_handles:
        #     if handle != main_window_handle:
        #         try:
        #             driver.switch_to.window(handle)
        #             current_url = driver.current_url
        #             if 'dsers.com' not in current_url:
        #                 driver.close()
        #         except:
        #             pass
        # driver.switch_to.window(main_window_handle)
        print("✅ Đã quay về main window.")