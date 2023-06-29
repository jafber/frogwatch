# frogcam

2023, Jan Berndt (me@jan-berndt.de)

# api
## /front
```
front > back {
	'type': 'auth',
	'session': 1234,
}
front > back {
	'type': 'get_image',
	'current_hash': 231 // 8-bit-uint created by XORing all bytes
}
front > back {
	'type': 'move_servo',
	'is_to_right': bool
}
back > front { blob }
```
## /raspi
```
back > raspi {
	'type': 'init_stream',
	'last_update': 12345
}
back > raspi {
	'type': 'move_servo',
	'is_to_right': bool
}
raspi > back { blob }
```


# Raspberry

## SSH
https://superuser.com/a/1013998/1139103
```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null pi@$(curl -s 'https://gist.githubusercontent.com/CheeseCrustery/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ipv4.txt')
```

## libcamera
```bash
libcamera-jpeg -o /www-data/frogcam/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000
```

## dyndns cron job
**WARNING**: /etc/cron.hourly only gets executed as root, which is not the right environment
```bash
sudo cp .notes/saveip .notes/dyndns /usr/bin/
sudo chmod 755 /usr/bin/saveip /usr/bin/dyndns
sudo echo '* *	* * *	pi	dyndns /var/log/cron/dyndns' >> /etc/crontab
sudo mkdir -p /var/log/cron/
sudo chmod -R 777 /var/log/cron/
sudo service cron start
```

## websockets session
/etc/supervisor/conf.d/frogcam.conf
```
[program:frogcam]
directory=/home/pi/frogcam/raspi
environment=PYTHONPATH=/usr/lib/python3/dist-packages
command=/home/pi/frogcam/.venv/bin/python raspi/__init__.py --url wss://jan-berndt.de/frogcam/ws/raspi --port 443
autostart=true
autorestart=true
stderr_logfile=/var/log/frogcam/raspi.err.log
stdout_logfile=/var/log/frogcam/raspi.out.log
```


# Server

## supervisor
```bash
sudo nano /etc/supervisor/conf.d/frogcam.conf
sudo supervisorctl reread
sudo service supervisor restart
sudo supervisorctl status
```

/etc/supervisor/conf.d/frogcam.conf
```
[program:frogcam]
directory=/home/frogcam/frogcam/
environment=PYTHONPATH=/usr/lib/python3/dist-packages
command=/home/pi/frogcam/app/.venv/bin/python ws.py --bind 127.0.0.1:8001
autostart=true
autorestart=true
stderr_logfile=/var/log/frogcam/ws.err.log
stdout_logfile=/var/log/frogcam/ws.out.log
```

## nginx
```bash
sudo nano /etc/nginx/sites-available/frogcam
sudo ln --symbolic /etc/nginx/sites-available/frogcam /etc/nginx/sites-enabled/
nginx -s reload
```

/etc/nginx/sites-available/frogcam
```
# http 'Upgrade' header is mapped to 'upgrade' by default, or 'close' if 'Connection' header is empty
map $http_upgrade $connection_upgrade {
	default upgrade;
	'' close;
}

server {
    # this needs to be merged with the default homepage config
	listen 80;
	server_name jan-berndt.de *.jan-berndt.de;

	# websocket camera stream
	location /frogcam/ws {
		# https://websockets.readthedocs.io/en/stable/howto/nginx.html
		# https://www.nginx.com/blog/websocket-nginx/
		proxy_pass http://127.0.0.1:8001/;
		proxy_http_version 1.1;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection $connection_upgrade;
		proxy_set_header Host $host;
	}

	# serve web app
	location /frogcam {
		alias /home/frogcam/frogcam/front/dist;
	}
}

```
