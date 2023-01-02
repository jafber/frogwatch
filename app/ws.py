from asyncio import run, Future
from argparse import ArgumentParser

from websockets import serve
from camera import Camera

camera = None

async def send_frames(websocket):
	async for message in websocket:
		f = camera.get_frame()
		await websocket.send(f)

async def main():
	global camera
	parser = ArgumentParser()
	parser.add_argument('--bind')
	args = parser.parse_args()
	split = args.bind.split(':')
	async with serve(send_frames, split[0], split[1]):
		print('serving')
		camera = Camera()
		await Future()

run(main())
