import asyncio
import logging
from os import getenv
import websockets
from connection_handler import ConnectionHandler
import os

# make logs look nice
def configure_logging():
    log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=date_format, level=logging.INFO)

# run a websocket server with a handler object to take care of connections
async def main(port):
    RASPI_TOKEN = getenv("RASPI_TOKEN")
    if not RASPI_TOKEN:
        raise EnvironmentError("RASPI_TOKEN environment variable is not set")
    handler = ConnectionHandler(RASPI_TOKEN)
    async with websockets.serve(handler.handle, "", port):
        await asyncio.Future()

if __name__ == '__main__':
    configure_logging()
    logging.info("hello world")
    asyncio.run(main(3000))
