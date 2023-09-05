import asyncio
import json
from time import time
import logging

import websockets
from websockets.exceptions import ConnectionClosed

class FrontConnection:
    def __init__(self, session, socket):
        self.session = session
        self.socket = socket
        self.is_waiting_for_image = False

IMAGE_TIMEOUT_S = 10
current_image_time = 0.0
current_image = bytes()
front_connections = {}
raspi_connection = None
log = None

# make logs look nice
def configure_logging():
    log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=date_format, level=logging.INFO)

# get image's identifier (8-bit-uint created by XORing all bytes)
def image_id(img):
    hash = 0
    for b in img:
        hash ^= b
    return hash

# try to send the msg object to the raspberry
async def send_to_raspi(msg):
    if raspi_connection and not raspi_connection.closed:
        await raspi_connection.send(json.dumps(msg))

# keep a connection to the frontend alive
async def handle_front(socket):
    # no authentication for now, just a session id
    logging.info('established new front connetion')
    msgraw = await socket.recv()
    logging.info(f'frontend received "{msgraw}"')
    auth = json.loads(msgraw)
    assert auth['type'] == 'auth'
    session = auth['session']
    assert not session in front_connections
    conn = FrontConnection(session, socket)
    front_connections[session] = conn
    try:
        while not socket.closed:
            msgraw = await socket.recv()
            logging.info(f'frontend received "{msgraw}"')
            msg = json.loads(msgraw)
            if msg['type'] == 'get_image':
                logging.info(f'received image request on frontend connection {session}')
                # send image directly if we have a new one
                if msg['current_hash'] != image_id(current_image) and time() - current_image_time < IMAGE_TIMEOUT_S:
                    conn.is_waiting_for_image = False
                    await socket.send(current_image)
                else:
                    conn.is_waiting_for_image = True
                # tell raspi to start streaming
                await send_to_raspi({
                    'type': 'init_stream',
                    'last_update': int(time()),
                })
            elif msg['type'] == 'move_servo':
                logging.info(f'moving servo to the {"right" if msg["is_to_right"] else "left"} according to frontend {session}')
                await send_to_raspi({
                    'type': 'move_servo',
                    'is_to_right': msg['is_to_right'],
                })
    except ConnectionClosed:
        logging.info(f'frontend {session} closed connection')
    finally:
        logging.info(f'terminating frontend connection {session}...')
        await socket.close()
        front_connections.pop(session)

# keep a connection to the raspi alive
async def handle_raspi(socket):
    global current_image, raspi_connection
    if raspi_connection and not raspi_connection.closed:
        logging.warning('raspi connection overwritten')
        await raspi_connection.close()
    logging.info('raspi connection established')
    raspi_connection = socket
    try:
        while not socket.closed:
            current_image = await socket.recv()
            logging.info(f'received image {image_id(current_image)}')
            # directly send image to all frontends that are currently waiting
            for conn in front_connections.values():
                if conn.is_waiting_for_image:
                    logging.info(f'sending image {image_id(current_image)} to conn {conn.session}')
                    await conn.socket.send(current_image)
    except ConnectionClosed:
        logging.warning('raspi closed connection')
    finally:
        logging.info('terminating raspi connection')
        await socket.close()
        raspi_connection = None

# handle an incoming ws connection
async def handler(conn):
    logging.info(f'got connection to {conn.path}')
    if conn.path.endswith('/front'):
        await handle_front(conn)
    elif conn.path.endswith('/raspi'):
        await handle_raspi(conn)

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()

if __name__ == '__main__':
    configure_logging()
    asyncio.run(main())
