from flask import Flask, Response
from camera import Camera
from servo import Servo

app = Flask(__name__)
servo = None

@app.route('/servo_left', methods=['POST'])
def servo_left():
	servo.step(-1)
	return {'step_val': servo.step_val}

@app.route('/servo_right', methods=['POST'])
def servo_right():
	servo.step(1)
	return {'step_val': servo.step_val}

if __name__ == '__main__':
	servo = Servo()
	try:
		app.run(host='0.0.0.0', debug=True, threaded=True)
	finally:
		servo.cleanup()
