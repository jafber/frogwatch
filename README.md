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

This will always run the container, even restarting with the environment variable after a reboot.
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

## Set Up Wireguard VPN

For development, I need to be able to SSH onto the PI from outside my parent's home network.
To acheive this, I have created a wireguard VPN for the PI.
WG-easy is running on https://wireguard.jan-berndt.de as the network access point.

### WG-easy

Add clients:

- `raspi, 10.8.0.2`
- `ideapad, 10.8.0.3`

### Raspi

Create the following `/etc/wireguard/wg0.conf`:

```
[Interface]
PrivateKey = ...
Address = 10.8.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = ...
PresharedKey = ...
AllowedIPs = 10.8.0.0/24
PersistentKeepalive = 25
Endpoint = wireguard.jan-berndt.de:51820
```

Then to enable `wg0` on startup:

```
sudo chown root:root /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

### Local access

Use this config locally:

```
[Interface]
PrivateKey = ...
Address = 10.8.0.3/24
DNS = 1.1.1.1

[Peer]
PublicKey = ...
PresharedKey = ...
AllowedIPs = 10.8.0.0/24
Endpoint = wireguard.jan-berndt.de:51820
```

Add this to `~/.ssh/config`:

```
Host raspi
    HostName 10.8.0.2
    User pi
```

Then connect to the VPN and `ssh raspi`

## Deploy to Raspberry PI

### Install Docker

```
sudo apt install docker
```


### libcamera

```bash
libcamera-jpeg -o /var/www/html/test.jpg
libcamera-vid --width 1080 --height 720 --framerate 5 --codec h264 --inline --listen -o tcp://0.0.0.0:8000
```
