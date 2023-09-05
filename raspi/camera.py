from time import time
from io import BytesIO
from threading import Thread

from picamera2 import Picamera2

class Camera:

    TIMEOUT_S = 10

    def __init__(self, log):
        self.log = log
        self.thread = None # threading.Thread of self.stream
        self.last_update = 0 # unix time float
        self.on_new_image = None # callback for the jpg blobs
        
        # init picamera2
        self.cam = Picamera2()
        cfg = self.cam.create_still_configuration(main={
            'size': (int(3280/2), int(2464/2))
        })
        self.cam.configure(cfg)
        self.cam.start()

    # if the thread is not already rolling, start it up
    def start_stream(self, on_new_image):
        self.last_update = time()
        self.on_new_image = on_new_image
        if self.thread is None:
            self.thread = Thread(target=self.stream)
            self.thread.start()

    # stop the thread
    def stop_stream(self):
        self.on_new_image = None
        self.last_update = 0

    # capture jpgs and send the blob to our callback until self.last_update times out
    def stream(self):
        self.log.info('camera starting thread')
        stream = BytesIO()
        while True:
            self.cam.capture_file(stream, format='jpeg')
            stream.seek(0)
            if self.on_new_image and time() - self.last_update < self.TIMEOUT_S:
                self.on_new_image(stream.read())
                stream.seek(0)
                stream.truncate()
            else:
                break
        self.log.info('camera stopping thread')
        self.thread = None
