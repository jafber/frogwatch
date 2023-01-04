# libcamera
libcamera-jpeg -o /www-data/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000

# dyndns cron job
cp .notes/saveip /bin/
chmod 755 /bin/saveip
gh config set editor saveip
cp .notes/dyndns /etc/cron.hourly
chmod 755 /etc/cron.hourly/dyndns

# supervisor
sudo cp ./supervisor-conf.d /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo service supervisor restart
sudo supervisorctl status

# curl
curl --cert testclient/cert.pem --key testclient/cert-key.pem --cacert ca.pem https://raspberry/
