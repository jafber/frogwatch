from asyncio import run, Future
from argparse import ArgumentParser
from json import loads

import websockets
from camera import Camera

async def main():
    parser = ArgumentParser()
    parser.add_argument('--url')
    args = parser.parse_args()
    camera = Camera()
    async for socket in websockets.connect(args.url):
        # we make our own image handler so the connectionclosed error is caught
        async def handle_new_image(blob):
            try:
                socket.send(blob)
            except websockets.ConnectionClosed:
                pass
        try:
            msg = loads(await socket.recv())
            assert msg['type'] == 'init_stream'
            camera.start_stream(handle_new_image)
        except websockets.ConnectionClosed:
            continue

if __name__ == '__main__':
    run(main())
