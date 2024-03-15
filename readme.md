# frogcam

2023, Jan Berndt (me@jan-berndt.de)

## API

### /front

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

### /raspi

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

## RASPBERRY

### SSH

https://superuser.com/a/1013998/1139103

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null pi@$(curl -s 'https://gist.githubusercontent.com/CheeseCrustery/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ipv4.txt')
```

### libcamera

```bash
libcamera-jpeg -o /var/www/html/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000
```

### dyndns cron job

**WARNING**: /etc/cron.hourly only gets executed as root, which is not the right environment

```bash
sudo cp .notes/saveip .notes/dyndns /usr/bin/
sudo chmod 755 /usr/bin/saveip /usr/bin/dyndns
sudo echo '* *	* * *	pi	dyndns /var/log/cron/dyndns' >> /etc/crontab
sudo mkdir -p /var/log/cron/
sudo chmod -R 777 /var/log/cron/
sudo service cron start
```

### occasional restart cron job so the process does not shit itself and die

```
34 *  * * *  root  supervisorctl restart frogcam
```

### websockets session

/etc/supervisor/conf.d/frogcam.conf

```
[program:frogcam]
directory=/home/pi/frogcam/raspi
environment=PYTHONPATH=/usr/lib/python3/dist-packages
command=/home/pi/frogcam/.venv/bin/python raspi/__init__.py --url wss://jan-berndt.de/frogcam/ws/raspi
autostart=true
autorestart=true
stderr_logfile=/var/log/frogcam/raspi.err.log
stdout_logfile=/var/log/frogcam/raspi.out.log
```

## BACKEND SERVER

### supervisor

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
command=/home/frogcam/frogcam/.venv/bin/python back/__init__.py --bind 127.0.0.1:8001
autostart=true
autorestart=true
stderr_logfile=/var/log/frogcam/back.err.log
stdout_logfile=/var/log/frogcam/back.out.log
```

### nginx

```bash
sudo nano /etc/nginx/sites-available/frogcam
sudo ln --symbolic /etc/nginx/sites-available/frogcam /etc/nginx/sites-enabled/
nginx -s reload
```

/etc/nginx/sites-available/homepage

```
map $http_upgrade $connection_upgrade {
	default upgrade;
	'' close;
}

server {
	listen 80;

	...

	# skip language check for frogcam
	location /frogcam {
		return 301 https://jan-berndt.de$request_uri;
	}
}

server {
	listen 443 ssl;

	...

	# frogcam websocket camera stream
	location /frogcam/ws {
		# https://websockets.readthedocs.io/en/stable/howto/nginx.html
		# https://www.nginx.com/blog/websocket-nginx/
		proxy_pass http://127.0.0.1:8001/;
		proxy_http_version 1.1;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection $connection_upgrade;
		proxy_set_header Host $host;
	}

	# frogcam html page
	location /frogcam {
		alias /home/frogcam/frogcam/front;
	}
}

```

## docker

```
docker build -t jan/frogcam .
docker run -d -p 3000:3000 jan/frogcam
```
