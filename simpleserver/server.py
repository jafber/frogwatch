import asyncio
import websockets

HOST = "0.0.0.0"
PORT = 8765

async def handle_connection(websocket):
    async for message in websocket:
        print(f"Received message: {message} on path {websocket.request.path}")
        await websocket.send("hello world")

async def main():
    server = await websockets.serve(handle_connection, HOST, PORT)
    print(f"WebSocket server started on ws://{HOST}:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
