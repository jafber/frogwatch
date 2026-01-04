import asyncio
import logging
from websockets.asyncio.server import serve
from connection_handler import ConnectionHandler
from http import HTTPStatus
from argparse import ArgumentParser

# Read the token for sending images to the server from Docker secret
def read_secret(secret_path):
    try:
        with open(secret_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Could not read secret token: {e}")
        return None

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
async def main(port, token):
    handler = ConnectionHandler(token)
    async with serve(handler.handle, "", port, process_request=health_check) as server:
        await server.serve_forever()

if __name__ == '__main__':
    configure_logging()
    parser = ArgumentParser()
    parser.add_argument(
        '--token', 
        help='Secret token for authentication', 
        default=read_secret("/run/secrets/raspi_token")
    )
    args = parser.parse_args()
    if not args.token:
        logging.error('No secret token provided via --token or Docker secret.')
        exit(1)

    logging.info("starting up")
    asyncio.run(main(3000), token)
