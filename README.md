# Frogwatch

Code for [frogwatch.jan-berndt.de](https://frogwatch.jan-berndt.de), a live camera stream of my family's frog terrarium, plus an automatic one-photo-per-day frog gallery.

A Raspberry Pi 3B+ runs [MediaMTX](https://github.com/bluenviron/mediamtx) with its built-in `rpiCamera` source (hardware H.264) and pushes the stream over encrypted SRT to a VPS. There, a second MediaMTX serves it as HLS, a Caddy container serves the static Svelte frontend and proxies the stream, and `photod` samples frames during the day and keeps the best frog photo of each day.

```
Pi 3B+ (Bullseye 32-bit)                    VPS (Coolify/Traefik)
┌──────────────────────────┐                ┌──────────────────────────────────────┐
│ mediamtx (systemd)       │  SRT :8890/udp │ mediamtx container                   │
│  rpiCamera → H.264 HW    │ ─────────────▶ │  ingest path /frog                   │
│  runOnReady: ffmpeg push │                │  ├─ HLS :8888 (internal)             │
│  Restart=always          │                │  └─ RTSP :8554 (internal)            │
└──────────────────────────┘                │        ▲              ▲              │
   WireGuard 10.8.0.2 (SSH only)            │  front (caddy)   photod (python)     │
                                            │   /        → static Svelte site      │
                                            │   /stream/ → proxy mediamtx:8888     │
                                            │   /photos/ → photos volume (ro)      │
                                            └──────────────────────────────────────┘
```

MediaMTX is pinned to **v1.19.2** everywhere (VPS image tag + Pi binary in `pi/setup.sh`). Upgrade both in lockstep.

## Try it out locally

```bash
cp .env.example secret.env        # fill in passwords (SRT_PASSPHRASE: 10-64 chars)
docker compose --env-file=secret.env -f docker-compose.yml -f docker-compose.local.yml up --build
```

Then publish a test pattern (needs a local ffmpeg with SRT — `scoop install ffmpeg` — or docker as fallback):

```bash
tools/mock-publish.sh
```

Open [http://localhost:8080](http://localhost:8080). Checks:

```bash
curl -f http://localhost:8080/healthz                   # OK
curl -fL http://localhost:8080/stream/frog/index.m3u8   # HLS manifest
curl -f http://localhost:8080/photos/index.json         # gallery dates
```

The local override samples a photo every minute with no daylight window; force a gallery rollover by backdating the candidate:

```bash
docker exec frogwatch-photod-1 python -c "import json,pathlib;p=pathlib.Path('/photos/candidate.json');m=json.loads(p.read_text());m['date']='2000-01-01';p.write_text(json.dumps(m))"
```

Calibrate photo scoring against sample images:

```bash
docker compose --env-file=secret.env run --rm -v ./photod/testdata:/data photod python photod.py --score /data/*.jpg
```

## Deploy frontend & backend to Coolify

- New resource > Public repository > `https://github.com/jafber/frogwatch`, docker-compose with `/docker-compose.yml`
- Domain **only on `front`**: `https://frogwatch.jan-berndt.de` (port 80). No domain on mediamtx/photod.
- Environment variables (runtime-available): `MTX_PUBLISH_USER`, `MTX_PUBLISH_PASS`, `SRT_PASSPHRASE`, `TZ`
- **Open UDP port 8890 in the VPS/cloud firewall** — SRT ingest bypasses Traefik entirely.
- Validate the public UDP path before touching the Pi: `tools/mock-publish.sh frogwatch.jan-berndt.de`

## Deploy to the Raspberry Pi

The Pi runs MediaMTX directly (systemd, no container — it needs the camera). Provision idempotently over SSH:

```bash
ssh raspi 'sudo bash -s' < pi/setup.sh   # first run creates /etc/frogwatch/frogwatch.env and stops
ssh raspi sudo nano /etc/frogwatch/frogwatch.env   # fill in VPS_HOST + secrets (same as Coolify)
ssh raspi 'sudo bash -s' < pi/setup.sh   # installs, starts, self-checks
```

The script pins MediaMTX v1.19.2 (sha256-verified), disables the legacy camera stack (may ask for one reboot), stops/purges the old supervisor app, installs the `frogwatch-cam` systemd service (`Restart=always`), enables the hardware watchdog, and ends with a PASS/FAIL self-check. It never touches `/etc/wireguard`.

Debugging on the Pi (over WireGuard):

```bash
ssh raspi journalctl -u frogwatch-cam -f
ffprobe rtsp://10.8.0.2:8554/cam          # raw camera stream, h264 1280x960
```

## Verification

| What | Command | Expect |
|---|---|---|
| Pi service | `ssh raspi systemctl is-active frogwatch-cam` | `active` |
| Camera→RTSP | `ffprobe rtsp://10.8.0.2:8554/cam` (on WG) | h264 1280x960 |
| VPS ingest | mediamtx container logs | `is publishing to path 'frog'` |
| HLS | `curl -fL https://frogwatch.jan-berndt.de/stream/frog/index.m3u8` | m3u8 |
| Site | `curl -f https://frogwatch.jan-berndt.de/healthz` | `OK` |
| Gallery | `curl -f https://frogwatch.jan-berndt.de/photos/index.json` | JSON array |

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
