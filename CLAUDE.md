# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Live camera stream of a frog terrarium ([frogwatch.jan-berndt.de](https://frogwatch.jan-berndt.de/index.html)). A Raspberry Pi captures JPEGs and pushes them over a WebSocket to a Python relay server, which fans them out to browser clients viewing a static vanilla HTML/JS page.

## Architecture

Three processes connected by WebSockets, all speaking the same protocol:

- **`back/`** — the relay server (`websockets` asyncio, listens on port 3000). Holds a single `current_image` in memory and never persists anything. One `ConnectionHandler` instance routes by URL path: `/ws/front` → browsers, `/ws/raspi` → the Pi. Entry point `back/__init__.py`; per-connection logic split into `front_connection.py` and `raspi_connection.py`.
- **`raspi/`** — runs on the Pi. `__init__.py` maintains the outbound WebSocket + auth; `camera.py` wraps `picamera2`, capturing JPEGs on a background thread only while requests are recent (10s timeout, `Camera.TIMEOUT_S`).
- **`front/`** — static site (no build step). `index.js` drives the canvas render loop and WebSocket lifecycle.

### Message protocol (JSON control frames + raw binary image frames)

- Front authenticates with `{type:'auth', session:<uuid>}`, then polls with `{type:'get_image', current_hash:<n>}`. Can also send `{type:'move_servo', is_to_right:<bool>}`.
- Raspi authenticates by sending the **raw token string** (not JSON) as its first frame, compared against `RASPI_TOKEN`.
- Server tells the Pi to start capturing with `{type:'init_stream', last_update:<unixtime>}`; the Pi replies with raw JPEG bytes, which the server forwards to any front with `is_waiting_for_image` set.
- **Image identity is an 8-bit XOR hash** of all image bytes (`current_image_id` in the backend, `blobHash` in `front/index.js`) — kept in sync on both sides so a client can skip re-sending an image it already has. Change one, change the other.

### Request flow (pull-based)

The front is the pacer: each received image triggers the next `get_image`. `get_image` both (a) returns the current image immediately if it's fresh + different, else marks the front as waiting, and (b) pokes the Pi via `init_stream` to keep capturing. The Pi self-stops capturing when no `init_stream` arrives within `TIMEOUT_S`.

## Running locally

```bash
echo "RASPI_TOKEN=super-secret-token" > secret.env
docker compose --env-file=secret.env up          # serves site + relay on :3000 (Caddy fronts back)
curl -f http://localhost:3000/ws/healthz         # -> OK (Caddy strips /ws, hits back's /healthz)
```

Simulate the Pi (sends pre-saved JPEGs from `mockpi/frog/`):

```bash
cd mockpi/ && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
SECRET_FILE=../secret.env python __init__.py ws://localhost:3000/ws
```

There is no test suite, linter, or build step. The front is served as-is.

## Deployment topology

- **Local / Coolify:** the two containers (`back`, `caddy`/`front`) are separate. Caddy (`Caddyfile`) serves `front/` statically and reverse-proxies `/ws*` → `back:3000`, stripping the `/ws` prefix — so backend routes are `/healthz`, `/front`, `/raspi` but clients hit `/ws/healthz`, `/ws/front`, `/ws/raspi`. `docker-compose.yml` uses Caddy; `docker-compose-coolify.yml` uses nginx (`Dockerfile`) for the front instead.
- **Raspberry Pi:** not containerized (needs direct camera hardware access). Run via `supervisor` using `raspi/frogwatch.conf`. `picamera2` is pre-installed system-wide, so the venv must be created with `--system-site-packages`.
- Coolify can't set `wss://` URLs explicitly; it upgrades `https://` to WebSocket automatically. Front hardcodes `wss://frogwatch.jan-berndt.de/ws/front` in `front/index.js` (`STREAM_URL`).

## Accessing the Pi (WireGuard VPN)

The Pi lives at the maintainer's parents' home, so there's no direct network access. A WireGuard instance runs on a VPS (WG-easy at `wireguard.jan-berndt.de`) that the Pi connects to automatically on boot. To reach the Pi, connect a laptop to the same VPN, then SSH in.

- Peers (see README for full config): Pi = `10.8.0.2`, laptop = `10.8.0.3`.
- Pi runs `wg-quick@wg0` as a systemd service (`PersistentKeepalive = 25`) so its tunnel is always up.
- SSH shortcut: `~/.ssh/config` `Host raspi` → `HostName 10.8.0.2`, `User pi`. Connect the VPN, then `ssh raspi`.

## Gotchas

- Backend URL routing is suffix-based (`path.endswith('/front')`), which is why the Caddy prefix-strip still works.
- `secret.env` and anything matching `*.env` are gitignored; never commit the token.
- The repo root also contains sibling scratch dirs (`../fetch_test`, `../swtest`, `../images`) that are experiments, not part of this app.
