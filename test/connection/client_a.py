import asyncio
import websockets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

async def listen():
    async with websockets.connect("ws://localhost:8765") as ws:
        print("Client A connected")
        driver = webdriver.Chrome()  # Chắc bạn đã cài ChromeDriver
        while True:
            msg = await ws.recv()
            print(f"Received: {msg}")
            if msg.startswith("client_id_a:"):
                search_query = msg.split(":", 1)[1]
                # Dùng Selenium mở Google và search
                driver.get("https://www.google.com")
                time.sleep(1)
                search_box = driver.find_element(By.NAME, "q")
                search_box.clear()
                search_box.send_keys(search_query)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)  # chờ kết quả hiển thị

asyncio.run(listen())
