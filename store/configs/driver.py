import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional
from selenium_stealth import stealth

STEALTH_JS = r"""
(() => {
    try {
        Object.defineProperty(navigator, "webdriver", {
            get: () => undefined,
            configurable: true
        });
    } catch (e) {}

    try {
        Object.defineProperty(navigator, "languages", {
            get: () => ["en-US", "en"],
            configurable: true
        });
    } catch (e) {}

    try {
        Object.defineProperty(navigator, "plugins", {
            get: () => [
                { name: "Chrome PDF Plugin" },
                { name: "Chrome PDF Viewer" }
            ],
            configurable: true
        });
    } catch (e) {}

    try {
        Object.defineProperty(navigator, "mimeTypes", {
            get: () => [
                { type: "application/pdf", suffixes: "pdf" }
            ],
            configurable: true
        });
    } catch (e) {}

    try {
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => {
            if (parameters.name === "notifications") {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };
    } catch (e) {}

    try {
        const getParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (p) {
            if (p === 37445) return "Intel Inc.";
            if (p === 37446) return "Intel Iris OpenGL Engine";
            return getParam.call(this, p);
        };
    } catch (e) {}

    try {
        if (typeof WebGL2RenderingContext !== "undefined") {
            const getParam2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function (p) {
                if (p === 37445) return "Intel Inc.";
                if (p === 37446) return "Intel Iris OpenGL Engine";
                return getParam2.call(this, p);
            };
        }
    } catch (e) {}

    try {
        Object.defineProperty(navigator, "hardwareConcurrency", {
            get: () => 4
        });
        Object.defineProperty(navigator, "deviceMemory", {
            get: () => 8
        });
    } catch (e) {}

    try {
        Object.defineProperty(navigator, "platform", {
            get: () => "Win32"
        });
    } catch (e) {}
})();
"""

def setup_driver() -> Optional[webdriver.Chrome]:
    try:
        print("Setting up Chrome WebDriver...")
        USER_AGENT = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())

        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={USER_AGENT}")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")

        user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")

        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-renderer-backgrounding")

        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # options.add_argument('--proxy-server=http://lkqbgbdk:klwsil8ci4hw@193.160.82.111:6083')

        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(3)

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        driver.execute_script("""
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
        """)

        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": USER_AGENT, "platform": "Windows"}
        )

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": STEALTH_JS})

        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        return driver
    except Exception as e:
        print(f"❌ Critical error initializing WebDriver. Details: {e}")
        print("Please check if Chrome is installed and no Selenium sessions are running in the background.")
        return None