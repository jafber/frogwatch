from argparse import ArgumentParser
from json import loads
import logging

import websockets.sync.client
from camera import Camera

def init_logger():
    log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=date_format)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger

def main(log):
    log.info('STARTING MAIN FUNCTION')
    parser = ArgumentParser()
    parser.add_argument('--url')
    args = parser.parse_args()
    camera = None
    while True:
        log.info(f'attempting connection to {args.url}')
        with websockets.sync.client.connect(args.url) as socket:
            log.info('connection established')
            # we make our own image handler so the connectionclosed error is caught
            def handle_new_image(blob):
                log.info('took new image, sending now')
                try:
                    socket.send(blob)
                except websockets.ConnectionClosed as e:
                    log.error(f'connection closed {e}')
            try:
                while True:
                    msg = loads(socket.recv())
                    assert msg['type'] == 'init_stream'
                    log.info(f'got message {msg}')
                    if not camera:
                        camera = Camera(log)
                    camera.start_stream(handle_new_image)
            except websockets.ConnectionClosed as e:
                log.error(f'connection closed {e}')

if __name__ == '__main__':
    logger = init_logger()
    main(logger)
