from asyncio import run, Future
from argparse import ArgumentParser

from websockets import serve
from camera import Camera

camera = None

async def listen_for_init(websocket):
	async def handle_new_image(img):
		await websocket.send(img)
	async for _ in websocket:
		camera.initialize(handle_new_image)

async def main():
	global camera
	parser = ArgumentParser()
	parser.add_argument('--url')
	parser.add_argument('--port')
	args = parser.parse_args()
	async with serve(listen_for_init, args.url, args.port):
		print('serving')
		camera = Camera()
		await Future()

if __name__ == '__main__':
    run(main())
