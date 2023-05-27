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
	parser.add_argument('--bind')
	args = parser.parse_args()
	split = args.bind.split(':')
	async with serve(listen_for_init, split[0], split[1]):
		print('serving')
		camera = Camera()
		await Future()

if __name__ == '__main__':
    run(main())
