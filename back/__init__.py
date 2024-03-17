import asyncio
import logging

import websockets

from connection_handler import ConnectionHandler

# make logs look nice
def configure_logging():
    log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=date_format, level=logging.INFO)

# run a websocket server with a handler object to take care of connections
async def main(port):
    handler = ConnectionHandler()
    async with websockets.serve(handler.handle, "", port):
        await asyncio.Future()

if __name__ == '__main__':
    configure_logging()
    asyncio.run(main(3000))
