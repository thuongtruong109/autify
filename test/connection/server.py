import asyncio
import websockets

data_list = [
    "client_id_a:python",
    "client_id_b:javascript",
    "client_id_a:openai",
    "client_id_b:nodejs"
]

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    try:
        while True:
            # gửi data từng entry trong data_list
            for item in data_list:
                await websocket.send(item)
                await asyncio.sleep(1)
            await asyncio.sleep(5)
    except websockets.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server started at ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
