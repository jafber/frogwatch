# Frogcam

2023, Jan Berndt (me@jan-berndt.de)

## Raspberry Pi

### ssh

https://superuser.com/a/1013998/1139103

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null pi@$(curl -s $DYNDNS_IP)
```

### libcamera

```bash
libcamera-jpeg -o /var/www/html/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000
```

### supervisor

```bash
cp raspi/scripts/frogcam.conf /etc/supervisor/conf.d
supervisorctl reload
```

### dyndns

```bash
cp raspi/scripts/dyndns raspi/scripts/saveip /usr/bin/
```

### cron

**WARNING**: /etc/cron.hourly only gets executed as root, which is not the right environment

`/etc/crontab`

```
* *     * * *   pi dyndns /var/log/cron/dyndns
34 *    * * *   root supervisorctl restart frogcam
```

## Server

### nginx

`/etc/nginx/sites-available/jan-berndt.de.conf`

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

### docker

```bash
chmod +x build run
./build
./run
```

## WSS API

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
