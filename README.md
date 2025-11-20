# Frogwatch

This is the code for [frogwatch.jan-berndt.de](https://frogwatch.jan-berndt.de/index.html), a live camera stream of my family's frog terrarium. The camera is attached to a Raspberry PI continually streaming JPG images to a python websockets server. The server then sends the images out to any web client looking at the static vanilla HTML/JS webpage.

## Try it out locally

To run the server locally, create a file with the secret passkey that your PI should use.

```bash
echo "RASPI_TOKEN=super-secret-token" > secret.env
```

Then simply start the application on port 3000 using the provided docker compose file.

```bash
docker compose --env-file=secret.env up
```

You should be able to open the site under [http://localhost:3000](http://localhost:3000).
Run a health check to see that the backend is up:

```bash
docker compose ps
# frogwatch-back-1 STATUS: healthy
curl -f http://localhost:3000/ws/healthz
# OK
```

To try actually sending pictures to the server, you can use the provided script `mockpi` that acts like the Raspberry PI, sending out some pre-saved images.

```bash
cd mockpi/
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
SECRET_FILE=../secret.env python __init__.py ws://localhost:3000/ws
```

You can even stream your own gifs using imagemagick!

```bash
apt install imagemagick
convert frog-sitting.gif -coalesce %d.jpg
```

## Deploy Frontend & Backend to Coolify

- Create new project "frogwatch"
- New resource > Public repository > `https://github.com/jafber/frogwatch`
- Use docker-compose with `/docker-compose-coolify.yml`
- Set domains
    - back `https://frogwatch.jan-berndt.de:3000/ws`
    - front `https://frogwatch.jan-berndt.de`
- Add raspberry pi access token as environment variable
    - Environment Variables > Enable "Use docker build secrets"
    - Add `RASPI_TOKEN`, make sure it is available at runtime
- Now when running mockpi, you should see the gif at `https://frogwatch.jan-berndt.de`

> *Note on domains:* Frontend calls `wss://frogwatch.jan-berndt.de/ws/front` and raspberry calls `wss://frogwatch.jan-berndt.de/ws/raspi`. Coolify does not support setting wss URLs explicitly. Instead, https will get upgraded to a websocket connection automatically.

## Deploy to Raspberry PI

These are mostly notes for myself, it gets hacky.

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

`crontab -e`

```
* *     * * *   pi dyndns /var/log/cron/dyndns
34 *    * * *   root supervisorctl restart frogcam
```
