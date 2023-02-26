import asyncio
import json
from time import time
from hashlib import md5

import websockets

current_image = None
front_connections = {}
raspi_connection = None

async def send_to_raspi(msg):
	if raspi_connection and not raspi_connection.closed:
		await raspi_connection.send(json.dumps(msg))

async def handle_front(conn):
	auth = json.loads(await conn.recv())
	assert auth['type'] == 'auth'
	session = auth['session']
	assert not session in front_connections
	front_connections[session] = {
		'ready_for_image': False,
		'conn': conn,
	}
	try:
		while not conn.closed:
			msg = json.loads(conn.recv())
			if msg['type'] == 'get_image':
				# send image directly if we have a new one
				if msg['current_hash'] == md5(current_image).digest()[:16]

				# tell raspi to start streaming
				await send_to_raspi({
					'type': 'init_stream',
					'last_update': int(time()),
				})
			elif msg['type'] == 'move_servo':
				await send_to_raspi({
					'type': 'move_servo',
					'is_to_right': msg['is_to_right'],
				})
	finally:
		front_connections.pop(session)

async def handle_raspi(conn):
	if not raspi_connection.closed:
		await raspi_connection.close()
	raspi_connection = conn
	while not conn.closed:
		msg_raw = conn.recv()
		if type(msg_raw) == bytes:
			current_image = msg_raw
		elif

async def handler(conn):
	if conn.path == '/front':
		await handle_front(conn)
	elif conn.path == '/raspi':
		await handle_raspi(conn)

async def main():
	async with websockets.serve(handler, "", 8001):
		await asyncio.Future()

if __name__ == "__main__":
	asyncio.run(main())
