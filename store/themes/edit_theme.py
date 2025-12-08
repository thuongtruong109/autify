from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.element import delay, highlight_element
import os
import sys

# Determine base path for resources
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

def edit_theme(driver: webdriver.Chrome, storeId: str):
    print("\n" + "="*60)
    print("🎨 EDIT THEME...")
    print("="*60)

    try:
        # 1. Vào trang themes
        themes_url = f"https://admin.shopify.com/store/{storeId}/themes/editor"
        print(f"Đang vào trang: {themes_url}")
        driver.get(themes_url)
        delay(3)



    except Exception as e:
        print(f"❌ Lỗi khi edit theme: {e}")
        print("="*60)