import asyncio
import websockets
import time
from sys import argv

async def send_timestamp():
    uri = argv[1] if len(argv) >= 2 else "ws://localhost:8765"
    print(f"connecting to {uri}")
    async with websockets.connect(uri) as websocket:
        while True:
            timestamp = str(time.time())
            await websocket.send(timestamp)
            print(f"Sent: {timestamp}")
            answer = await websocket.recv()
            print(f"Recv: {answer}")
            await asyncio.sleep(3)

asyncio.run(send_timestamp())