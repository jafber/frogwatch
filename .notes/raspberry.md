# libcamera
libcamera-jpeg -o /www-data/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000

# dyndns cron job
**WARNING**: /etc/cron.hourly only gets executed as root, which is not the right environment
sudo cp .notes/saveip .notes/dyndns /usr/bin/
sudo chmod 755 /usr/bin/saveip /usr/bin/dyndns
sudo echo '* *	* * *	pi	dyndns /var/log/cron/dyndns' >> /etc/crontab
sudo mkdir -p /var/log/cron/
sudo chmod -R 777 /var/log/cron/
sudo service cron start

# supervisor
sudo cp ./supervisor-conf.d /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo service supervisor restart
sudo supervisorctl status

# nginx
sudo cp ~/frogcam/.notes/nginx /etc/nginx/sites-available/frogcam
sudo ln --symbolic /etc/nginx/sites-available/frogcam /etc/nginx/sites-enabled/
nginx -s reload

# frontend
sudo mkdir -p /www-data/frogcam
sudo rm -r /www-data/frogcam/*
sudo cp -r ~/frogcam/front/build/* /www-data/frogcam/
sudo chown www-data -R /www-data/frogcam/

# curl
curl --cert testclient/cert.pem --key testclient/cert-key.pem --cacert ca.pem https://raspberry/
