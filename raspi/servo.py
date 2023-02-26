from RPi import GPIO
import time

class Servo:

	max_step = 3

	def __init__(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(11, GPIO.OUT)
		self.servo = GPIO.PWM(11, 50)
		self.step_val = 0
		self.servo.start(0)
		self.set_servo()
	
	@staticmethod
	def clamp(val):
		return max(min(val, Servo.max_step), -Servo.max_step)

	def get_duty(self):
		deg = 90 + self.step_val * 30
		duty = 2 + (deg/180) * 10
		return duty
	
	def set_servo(self):
		self.servo.ChangeDutyCycle(self.get_duty())
		time.sleep(0.5)
		self.servo.ChangeDutyCycle(0)
	
	def step(self, val):
		new = self.clamp(self.step_val + val)
		if new != self.step_val:
			self.step_val = new
			self.set_servo()

	def cleanup(self):
		self.servo.stop()
		GPIO.cleanup()
