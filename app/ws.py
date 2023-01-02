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
	ip = args.split(':')[0]
	port = args.split(':')[1]
	async with serve(send_frames, ip, port):
		print('serving')
		camera = Camera()
		await Future()

run(main())
