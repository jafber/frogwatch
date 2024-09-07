from time import time
import logging

class RaspiConnection:
    def __init__(self, socket, handler):
        self.socket = socket
        self.handler = handler

    # generate a message for starting the stream
    def init_msg():
        return {
            'type': 'init_stream',
            'last_update': int(time()),
        }

    # generate a message for moving the servo motor
    def servo_msg(is_to_right):
        return {
            'type': 'move_servo',
            'is_to_right': is_to_right,
        }

    # keep the connection open and respond to requests
    async def keep_open(self):
        while not self.socket.closed:
            self.handler.current_image = await self.socket.recv()
            # logging.info(f'received image {self.handler.current_image_id()}')
            # directly send image to all frontends that are currently waiting
            for conn in self.handler.fronts.values():
                if conn.is_waiting_for_image:
                    logging.info(f'sending image {self.handler.current_image_id()} to conn {conn.session}')
                    await conn.socket.send(self.handler.current_image)
