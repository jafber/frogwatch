from time import time, sleep
from io import BytesIO
from threading import Thread

from picamera2 import Picamera2

class Camera:

	TIMEOUT_S = 10

	def __init__(self):
		self.thread = None
		self.frame = None
		self.last_access = 0
		self.cam = Picamera2()
		self.cam.start()

	def initialize(self):
		if self.thread is None:
			self.thread = Thread(target=self._thread)
			self.thread.start()
			while self.frame is None:
				sleep(0.1)

	def get_frame(self):
		self.last_access = time()
		self.initialize()
		return self.frame

	def _thread(self):
		stream = BytesIO()
		print('starting thread')
		while time() - self.last_access < self.TIMEOUT_S:
			self.cam.capture_file(stream, format='jpeg')
			stream.seek(0)
			self.frame = stream.read()
			stream.seek(0)
			stream.truncate()
		print('stopping thread')
		self.thread = None
