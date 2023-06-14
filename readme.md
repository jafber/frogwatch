# frogcam

# api
## /front
```
front > back {
	'type': 'auth',
	'session': 1234,
}
front > back {
	'type': 'get_image',
	'current_hash': 'jpoirmg;sdf' (first 16 digits of md5)
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

# Snippets

## libcamera
```bash
libcamera-jpeg -o /www-data/frogcam/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000
```

## curl
```bash
curl --cert testclient/cert.pem --key testclient/cert-key.pem --cacert ca.pem https://raspberry/
```

# Installation

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

# supervisor
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

# nginx
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
	listen 80;
	server_name raspberry;

	# websocket camera stream
	location /ws {
		# https://websockets.readthedocs.io/en/stable/howto/nginx.html
		# https://www.nginx.com/blog/websocket-nginx/
		proxy_pass http://127.0.0.1:8001/;
		proxy_http_version 1.1;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection $connection_upgrade;
		proxy_set_header Host $host;
	}

	# serve web app
	location / {
		root /www-data/frogcam;
	}
}

```

# frontend
```bash
sudo rm -r /www-data/frogcam/ 2> /dev/null
sudo mkdir -p /www-data/frogcam/
sudo cp -r ~/frogcam/front/dist/* /www-data/frogcam/
sudo chown www-data -R /www-data/frogcam/
sudo certbot certonly --dry-run --standalone -d www.jan-berndt.de -d jan-berndt.de -d www.dein-schoenstes-i.ch -d dein-schoenstes-i.ch -d xn--dein-schnstes-ich-6zb.de -d www.xn--dein-schnstes-ich-6zb.de
```
