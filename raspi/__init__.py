from argparse import ArgumentParser
from json import loads
import logging
from os import getenv
import websockets.sync.client
from camera import Camera

log = None
camera = None

# Read the token for sending images to the server from Docker secret
def read_secret(secret_path):
    try:
        with open(secret_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Could not read secret token: {e}")
        return None

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
def main(url, token):
    log.info('STARTING MAIN FUNCTION')
    while True:
        log.info(f'attempting connection to {url}')
        with websockets.sync.client.connect(url) as socket:
            log.info('connection established, authenticating...')
            socket.send(token)
            log.info('authenticated')
            send_images(socket)

if __name__ == '__main__':
    log = init_logger()
    parser = ArgumentParser()
    parser.add_argument(
        '--url', 
        help='WebSocket endpoint URL', 
        default=getenv("WS_URL")
    )
    parser.add_argument(
        '--token', 
        help='Secret token for authentication', 
        default=read_secret("/run/secrets/raspi_token")
    )
    args = parser.parse_args()
    if not args.url:
        log.error('No WebSocket URL provided via --url or WS_URL env variable.')
        exit(1)
    if not args.token:
        log.error('No secret token provided via --token or Docker secret.')
        exit(1)

    main(args.url, args.token)
