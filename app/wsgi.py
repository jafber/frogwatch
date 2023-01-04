from flask import Flask, request, Blueprint

from servo import Servo

app = Flask(__name__)
api = Blueprint('api', __name__, url_prefix='/api')
servo = None

@api.route('/')
def index():
	return {'ok': True}

@api.route('/servo_left', methods=['POST'])
def servo_left():
	servo.step(-1)
	return {'step_val': servo.step_val}

@api.route('/servo_right', methods=['POST'])
def servo_right():
	servo.step(1)
	return {'step_val': servo.step_val}

if __name__ == '__main__':
	servo = Servo()
	try:
		app.register_blueprint(api)
		app.run(host='0.0.0.0', debug=True, threaded=True)
	finally:
		servo.cleanup()
