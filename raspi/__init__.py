from argparse import ArgumentParser
from json import loads

import websockets
from camera import Camera

def main():
    parser = ArgumentParser()
    parser.add_argument('--url')
    args = parser.parse_args()
    camera = Camera()
    while True:
        print('attempting connection...')
        with websockets.sync.client.connect(args.url) as socket:
            # we make our own image handler so the connectionclosed error is caught
            def handle_new_image(blob):
                print('sending image')
                try:
                    socket.send(blob)
                except websockets.ConnectionClosed:
                    print('connection closed')
            try:
                msg = loads(socket.recv())
                assert msg['type'] == 'init_stream'
                camera.start_stream(handle_new_image)
            except websockets.ConnectionClosed:
                print('connection closed')

if __name__ == '__main__':
    main()
