from argparse import ArgumentParser
from json import loads
import logging

import websockets.sync.client
from camera import Camera

log = None
camera = None

# create a logger
def init_logger():
    log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=date_format)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger

# keep the socket open and start streaming images when requested
def send_images(socket):
    global camera

    # we make our own image handler so the connectionclosed error is caught
    def handle_new_image(blob):
        log.info('took new image, sending now')
        try:
            socket.send(blob)
        except websockets.ConnectionClosed as e:
            log.error(f'connection closed {e}')
    
    # when we get a ping, start streaming
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

# continually open up connections to server and wait for image requests
def main(url):
    log.info('STARTING MAIN FUNCTION')
    while True:
        log.info(f'attempting connection to {url}')
        with websockets.sync.client.connect(url) as socket:
            log.info('connection established')
            send_images(socket)

if __name__ == '__main__':
    log = init_logger()
    parser = ArgumentParser()
    parser.add_argument('--url')
    args = parser.parse_args()
    main(args.url)
