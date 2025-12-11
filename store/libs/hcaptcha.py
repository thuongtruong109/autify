"""
Module để giải quyết hCaptcha sử dụng Bright Data Web Unlocker API
Docs: https://docs.brightdata.com/scraping-automation/web-unlocker/introduction

Module này KHÔNG phụ thuộc vào auth.py để tránh circular import.
Auth module sẽ gọi các hàm trong module này khi cần.
"""

import requests
import time
from typing import Optional, Dict


class BrightCaptchaSolver:
    """
    Sử dụng Bright Data Web Unlocker API để tự động bypass captcha
    Đơn giản theo đúng docs: https://api.brightdata.com/request
    """
    def __init__(self, api_key: str, zone: str = "web_unlocker1"):
        """
        Args:
            api_key: Bright Data API key
            zone: Tên zone (mặc định: "web_unlocker1")
        """
        self.api_key = api_key
        self.zone = zone
        self.base_url = "https://api.brightdata.com/request"

    def solve_hcaptcha(self, url: str, format: str = "raw") -> Optional[str]:
        """
        Lấy HTML/JSON từ URL qua Web Unlocker - tự động bypass captcha

        Args:
            url: URL cần access (ví dụ: https://accounts.shopify.com)
            format: "raw" = HTML, "json" = JSON response

        Returns:
            HTML/JSON content đã bypass captcha, hoặc None nếu thất bại
        """
        print(f"\n🚀 Đang bypass hCaptcha qua Bright Data Web Unlocker...")
        print(f"   URL: {url}")
        print(f"   Zone: {self.zone}")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "zone": self.zone,
                "url": url,
                "format": format
            }

            print("   ⏳ Đang gửi request đến Bright Data API...")
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()

            print(f"   ✅ Thành công! Nhận được {len(response.text)} bytes")
            print(f"   ✅ Captcha đã được bypass tự động!")

            return response.text

        except requests.exceptions.HTTPError as e:
            print(f"   ❌ Lỗi HTTP: {e}")
            if 'response' in locals():
                print(f"   Response: {response.text[:200]}...")
            return None
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            return None

    def get_json(self, url: str) -> Optional[Dict]:
        """
        Lấy JSON response qua Web Unlocker
        """
        result = self.solve_hcaptcha(url, format="json")
        if result:
            try:
                import json
                return json.loads(result)
            except:
                return None
        return None

    def inject_html_to_driver(self, driver, html_content: str) -> bool:
        """
        Inject HTML content (đã bypass captcha) vào Selenium driver

        Args:
            driver: Selenium WebDriver instance
            html_content: HTML đã bypass captcha từ Bright Data

        Returns:
            True nếu inject thành công
        """
        try:
            print("   ⏳ Đang inject HTML content vào browser...")

            # Replace toàn bộ HTML
            driver.execute_script(f"document.open(); document.write({repr(html_content)}); document.close();")

            time.sleep(2)

            print("   ✅ Đã inject HTML thành công!")
            return True

        except Exception as e:
            print(f"   ❌ Lỗi khi inject HTML: {e}")
            return False


def solve_shopify_hcaptcha(origin_url: str, api_key: str, zone: str) -> Optional[str]:
    """
    Bypass hCaptcha sử dụng Bright Data Web Unlocker.

    KHÔNG CẦN DRIVER! Chỉ cần origin URL và API key.
    Module auth.py sẽ tự xử lý việc extract origin và inject kết quả.

    Args:
        origin_url: URL trang chứa captcha (ví dụ: https://accounts.shopify.com)
        api_key: Bright Data API key
        zone: Tên zone (mặc định: "web_unlocker1")

    Returns:
        HTML content đã bypass captcha, hoặc None nếu thất bại
    """
    try:
        print("\n🔍 Đang bypass hCaptcha qua Bright Data Web Unlocker...")

        if not origin_url:
            print("❌ Thiếu origin URL")
            return None

        # Lấy HTML đã bypass captcha qua Web Unlocker API
        solver = BrightCaptchaSolver(api_key, zone)
        html_content = solver.solve_hcaptcha(origin_url)

        if not html_content:
            print("❌ Không thể lấy HTML từ Web Unlocker")
            return None

        print("✅ Đã nhận được HTML đã bypass captcha!")
        return html_content

    except Exception as e:
        print(f"❌ Lỗi khi bypass Shopify hCaptcha: {e}")
        return None
