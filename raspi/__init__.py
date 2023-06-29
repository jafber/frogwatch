from argparse import ArgumentParser
from json import loads

import websockets.sync.client
from camera import Camera

def main():
    parser = ArgumentParser()
    parser.add_argument('--url')
    args = parser.parse_args()
    camera = Camera()
    with open('/home/pi/frogcam/mockpi/testimage/testimage.jpg', 'rb') as f:
        blob = f.read()
    while True:
        print('attempting connection...')
        with websockets.sync.client.connect(args.url) as socket:
            print('connection established')
            # we make our own image handler so the connectionclosed error is caught
            def handle_new_image(blob):
                print('sending image')
                try:
                    socket.send(blob)
                except websockets.ConnectionClosed as e:
                    print(f'aaaaconnection closed {e}')
            try:
                while True:
                    msg = loads(socket.recv())
                    assert msg['type'] == 'init_stream'
                    print(f'got message {msg}')
                    camera.start_stream(handle_new_image)
            except websockets.ConnectionClosed:
                print('connection closed')

if __name__ == '__main__':
    main()
