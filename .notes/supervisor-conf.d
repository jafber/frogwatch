[program:frogcam]
directory=/home/pi/frogcam/app
command='PYTHONPATH=/usr/lib/python3/dist-packages /home/pi/frogcam/app/.venv/bin/gunicorn wsgi:app'
autostart=true
autorestart=true
stderr_logfile=/var/log/frogcam/wsgi.err.log
stdout_logfile=/var/log/frogcam/wsgi.out.log
