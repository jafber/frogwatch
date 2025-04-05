import asyncio
import websockets
import time

async def send_timestamp():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        while True:
            timestamp = str(time.time())
            await websocket.send(timestamp)
            print(f"Sent: {timestamp}")
            answer = await websocket.recv()
            print(f"Recv: {answer}")
            await asyncio.sleep(3)

asyncio.run(send_timestamp())