from time import time
import json
import logging

from websockets.exceptions import ConnectionClosed

from front_connection import FrontConnection
from raspi_connection import RaspiConnection

class ConnectionHandler:

    IMAGE_TIMEOUT_S = 10

    def __init__(self):
        self.current_image_time = 0.0
        self.current_image = bytes()
        self.fronts = {}
        self.raspi = None

    # send message to raspi
    async def send_to_raspi(self, msg):
        if self.raspi:
            await self.raspi.socket.send(json.dumps(msg))

    # get image's identifier (8-bit-uint created by XORing all bytes)
    def current_image_id(self):
        hash = 0
        for b in self.current_image:
            hash ^= b
        return hash

    # return true when the current image is not older than IMAGE_TIMEOUT_S
    def current_image_valid(self):
        return time() - self.current_image_time < self.IMAGE_TIMEOUT_S

    # register a new front connection and do stuff with it
    async def handle_front(self, socket):
        logging.info('established new front connection')
        conn = FrontConnection(socket, self)
        session = await conn.authenticate()
        assert not session in self.fronts
        logging.info(f'authenticated session {session}')
        self.fronts[session] = conn
        try:
            await conn.keep_open()
        except ConnectionClosed:
            logging.info(f'frontend {session} closed connection')
        finally:
            logging.info(f'terminating frontend connection {session}...')
            await socket.close()
            self.fronts.pop(session)

    # register a new raspi connection and do stuff with it
    async def handle_raspi(self, socket):
        if self.raspi and not self.raspi.socket.closed:
            logging.warning('raspi connection overwritten')
            await self.raspi.socket.close()
        logging.info('raspi connection established')
        self.raspi = RaspiConnection(socket, self)
        try:
            await self.raspi.keep_open()
        except ConnectionClosed:
            logging.warning('raspi closed connection')
        finally:
            logging.info('terminating raspi connection')
            await socket.close()
            self.raspi = None

    # handle incoming connections
    async def handle(self, conn):
        logging.info(f'got connection to {conn.path}')
        if conn.path.endswith('/front'):
            await self.handle_front(conn)
        elif conn.path.endswith('/raspi'):
            await self.handle_raspi(conn)
        else:
            logging.warning(f'unknown connection path {conn.path}')
            await conn.close()
