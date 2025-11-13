import asyncio
import websockets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

async def listen():
    async with websockets.connect("ws://localhost:8765") as ws:
        print("Client B connected")
        driver = webdriver.Chrome()
        while True:
            msg = await ws.recv()
            print(f"Received: {msg}")
            if msg.startswith("client_id_b:"):
                search_query = msg.split(":", 1)[1]
                driver.get("https://www.google.com")
                time.sleep(1)
                search_box = driver.find_element(By.NAME, "q")
                search_box.clear()
                search_box.send_keys(search_query)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)

asyncio.run(listen())
