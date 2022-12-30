from asyncio import run, Future

from websockets import serve
from camera import Camera

camera = None

async def echo(websocket):
	async for message in websocket:
		f = camera.get_frame()
		await websocket.send(f)

async def main():
	global camera
	async with serve(echo, "0.0.0.0", 5000):
		print('serving')
		camera = Camera()
		await Future()

run(main())
