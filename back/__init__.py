import asyncio
import logging
from os import getenv
from websockets.asyncio.server import serve
from connection_handler import ConnectionHandler
from http import HTTPStatus

# make logs look nice
def configure_logging():
    log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=date_format, level=logging.INFO)

# https://websockets.readthedocs.io/en/stable/faq/server.html#how-do-i-implement-a-health-check
# curl http://localhost:3000/healthz
def health_check(connection, request):
    if request.path == "/healthz":
        logging.info("health check OK")
        return connection.respond(HTTPStatus.OK, "OK\n")

# run a websocket server with a handler object to take care of connections
async def main(port):
    RASPI_TOKEN = getenv("RASPI_TOKEN")
    if not RASPI_TOKEN:
        raise EnvironmentError("RASPI_TOKEN environment variable is not set")
    handler = ConnectionHandler(RASPI_TOKEN)
    async with serve(handler.handle, "", port, process_request=health_check) as server:
        await server.serve_forever()

if __name__ == '__main__':
    configure_logging()
    logging.info("starting up")
    asyncio.run(main(3000))
