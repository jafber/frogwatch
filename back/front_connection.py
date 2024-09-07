import json
import logging

from raspi_connection import RaspiConnection

class FrontConnection:
    def __init__(self, socket, handler):
        self.session = ''
        self.socket = socket
        self.is_waiting_for_image = False
        self.handler = handler

    # receive auth message (just session id for now)
    async def authenticate(self):
        msgraw = await self.socket.recv()
        logging.info(f'frontend received "{msgraw}"')
        auth = json.loads(msgraw)
        assert auth['type'] == 'auth'
        self.session = auth['session']
        return self.session

    # act on messages requesting to move the servo or send a new image
    async def handle_msg(self, msg):
        if msg['type'] == 'get_image':
            logging.info(f'received image request on frontend connection {self.session}')
            # send image directly if we have a new one
            if msg['current_hash'] != self.handler.current_image_id and self.handler.current_image_valid:
                self.is_waiting_for_image = False
                await self.socket.send(self.handler.current_image)
            else:
                self.is_waiting_for_image = True
            # tell raspi to start streaming
            raspi_msg = RaspiConnection.init_msg()
            await self.handler.send_to_raspi(raspi_msg)
        elif msg['type'] == 'move_servo':
            logging.info(f'moving servo to the {"right" if msg["is_to_right"] else "left"} according to frontend {self.session}')
            raspi_msg = RaspiConnection.servo_msg(msg['is_to_right'])
            await self.handler.send_to_raspi(raspi_msg)

    # keep the connection open and respond to requests
    async def keep_open(self):
        while not self.socket.closed:
            msgraw = await self.socket.recv()
            logging.info(f'frontend received "{msgraw}"')
            msg = json.loads(msgraw)
            await self.handle_msg(msg)
