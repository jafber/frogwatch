# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Live camera stream of a frog terrarium ([frogwatch.jan-berndt.de](https://frogwatch.jan-berndt.de)) plus an automatic one-photo-per-day gallery. A Raspberry Pi 3B+ (Raspbian Bullseye 32-bit) runs MediaMTX with the embedded `rpiCamera` source and pushes H.264 over encrypted SRT to a VPS, where a second MediaMTX serves HLS. No custom streaming code — the app-specific parts are the Svelte frontend, the `photod` photo picker, and the provisioning/config files.

**MediaMTX is pinned to v1.19.2 everywhere** — the Docker image tag in `docker-compose.yml` and the binary version + sha256 in `pi/setup.sh`. Upgrade both in lockstep; config schema and `rpiCamera` params drift across minors.

## Architecture

- **Pi** (`pi/`): MediaMTX systemd service `frogwatch-cam` reads the camera (`rtsp://localhost:8554/cam`, 1280x960@25 full-FoV hardware H.264, sensor mode pinned via `rpiCameraMode`) and pushes via `runOnReady: ffmpeg -c copy` to the VPS — SRT primary (`PUSH_MODE=srt`), RTSP/TCP fallback. Provisioned by `pi/setup.sh` (idempotent, run via `ssh raspi 'sudo bash -s' < pi/setup.sh`); it renders `pi/mediamtx.yml.tpl` with envsubst from `/etc/frogwatch/frogwatch.env` into `/etc/frogwatch/mediamtx.yml`. setup.sh fetches the template/unit from GitHub main when run via stdin — push changes before re-provisioning.
- **VPS** (`docker-compose.yml`, Coolify): three containers.
  - `mediamtx`: SRT ingest :8890/udp (only host-published port; must also be open in the cloud firewall), internal HLS :8888 (classic fmp4, 2s segments) and RTSP :8554. Config `vps/mediamtx.yml`; secrets injected as `MTX_*` env overrides (`MTX_PATHS_FROG_SRTPUBLISHPASSPHRASE`, `MTX_AUTHINTERNALUSERS_1_USER/_PASS`) — MediaMTX does **not** expand `${VAR}` inside the yml. Auth: anonymous read-only (index 0), publisher user (index 1) publish-only on path `frog`.
  - `front`: multi-stage build, Vite/Svelte → `caddy:2-alpine`. Caddy is the single HTTP entry point: `/healthz`, `/stream/*` → proxy mediamtx:8888 (prefix stripped), `/photos/*` → photos volume, rest static.
  - `photod`: samples `rtsp://mediamtx:8554/frog` via ffmpeg during the daylight window, scores frames (HSV red/blue fraction, Laplacian blur gate), keeps a candidate on the `photos` volume, and at day rollover publishes `/photos/<date>.jpg` + regenerates `index.json` (self-healing by globbing).
- **Frontend** (`front/`): Svelte 5 + Vite, no SSR. `Player.svelte` (hls.js, dynamically imported; Safari uses native HLS; self-healing retry/backoff + offline overlay). Controls are media-chrome web components — play/pause + fullscreen only, deliberately no timeline/scrub bar (live stream; un-pausing jumps back to the live edge). `Gallery.svelte` (fetches `/photos/index.json` = JSON array of `YYYY-MM-DD` strings, images at `/photos/<date>.jpg`).

### Gotchas

- **MediaMTX HLS cookie flow (1.19)**: first manifest request gets a 302 to `?cookieCheck=1` + cookies, and segment requests need the `hlsSession` cookie. The redirect `Location` loses the `/stream` prefix — `front/Caddyfile` rewrites it back (`header_down Location ^/ /stream/`). Don't remove that line. When testing with curl, use `-L` and a cookie jar.
- SRT passphrase must be 10–64 chars (Pi's ffmpeg 4.3 caps at 64). Credentials must stay URL-safe — they're embedded in the SRT `streamid` and RTSP URL.
- `secret.env` / `*.env` are gitignored (`.env.example` is the template — same var names locally, in Coolify, and in `/etc/frogwatch/frogwatch.env` on the Pi).
- The Pi is reached over WireGuard only (`ssh raspi` = 10.8.0.2, see README). `pi/setup.sh` must never touch `/etc/wireguard`.
- Front build is Docker-only in prod; locally `npm run dev` in `front/` proxies `/stream` + `/photos` to the compose stack on :8080.

## Running locally

```bash
cp .env.example secret.env   # fill in
docker compose --env-file=secret.env -f docker-compose.yml -f docker-compose.local.yml up --build
tools/mock-publish.sh        # test pattern → SRT (local ffmpeg or docker fallback)
# site: http://localhost:8080 ; photod samples every 1min in the local override
```

Score calibration: `docker compose --env-file=secret.env run --rm -v ./photod/testdata:/data photod python photod.py --score /data/*.jpg` (positives ≈0.035 color score, negatives 0, blurry rejected by sharpness gate).

There is no test suite or linter; shell scripts pass shellcheck, front builds with `npm run build`.
