# Frogwatch Overhaul — MediaMTX Stream + Daily Frog Photo

## Context

Current frogwatch (https://frogwatch.jan-berndt.de) streams JPEGs from a Pi 3B+ over a custom WebSocket relay (Python `back/`) to a canvas-painting frontend. Fragile, breaks frequently. Goal: replace with battle-tested streaming stack, add automatic 1-photo-per-day frog gallery, maximize self-healing/uptime. Repo: `C:\Users\Jan\meine\hack\frogwatch\frogwatch`.

**User decisions:** HLS playback (few-sec latency fine, robust through Coolify/Traefik). Servo feature dropped (no hardware). Pi stays Raspbian Bullseye 32-bit, provisioned in-place over SSH (no SD flash). WireGuard SSH setup untouched. Photos day-window only (lights on timer, default 08–20, Europe/Berlin).

**Validated stack (researched):** MediaMTX on both ends. Pi: single static armv7 binary, `rpiCamera` source (embedded libcamera — works on Bullseye 32-bit, no system deps), hardware H.264 encode (Pi3B+ proven to 720p60). Push to VPS via `runOnReady: ffmpeg -c copy` (MediaMTX has no native outbound push; this is the documented pattern, `runOnReadyRestart: yes`). Primary transport SRT (encrypted, loss-tolerant UDP). **SRT verified on the actual Pi (2026-07-06):** ffmpeg `4:4.3.9-0+deb11u1+rpt1` installed, links `libsrt1.4-gnutls 1.4.2`; `ffmpeg -protocols` lists `srt` for input+output; `-h protocol=srt` shows `-passphrase` (size range 10..64) and `-enforced_encryption`. RTSP/TCP publish variant kept only as cheap insurance in the template. VPS: MediaMTX container serves classic fmp4 HLS internally; caddy front proxies it. Photo selection on VPS by frame-grabbing the stream — keeps Pi single-purpose, no camera contention.

## Target architecture

```
Pi 3B+ (Bullseye 32-bit)                    VPS (Coolify/Traefik)
┌──────────────────────────┐                ┌──────────────────────────────────────┐
│ mediamtx (systemd)       │  SRT :8890/udp │ mediamtx container                   │
│  rpiCamera → H.264 HW    │ ─────────────▶ │  ingest path /frog                   │
│  runOnReady: ffmpeg push │  (fallback     │  ├─ HLS :8888 (internal)             │
│  Restart=always          │   RTSP/TCP)    │  └─ RTSP :8554 (internal)            │
└──────────────────────────┘                │        ▲              ▲              │
   WireGuard 10.8.0.2 unchanged             │  front (caddy)   photod (python)     │
   (SSH only; independent failure           │   /        → static + hls.js         │
    domain from stream)                     │   /stream/ → proxy mediamtx:8888     │
                                            │   /photos/ → photos volume (ro)      │
                                            └──────────────────────────────────────┘
                                              Traefik: frogwatch.jan-berndt.de → front:80
```

Front caddy = single HTTP entry point (one Coolify domain, no strip-prefix gymnastics). Only host-published port: 8890/udp SRT ingest (+8554/tcp only if RTSP fallback needed).

## Repo changes

**Delete:** `back/`, `mockpi/`, `raspi/*` (old app), `Caddyfile`, root `Dockerfile`, `docker-compose-coolify.yml`, old `front/index.html|index.js|styles.css`. **Keep:** `front/img/*` → `front/public/img/*`, `favicon.ico`, `robots.txt`, branding (colors/logo carried into Svelte components).

**Create:**
```
docker-compose.yml            # Coolify: mediamtx + front + photod
docker-compose.local.yml      # local override: front on :8080
.env.example                  # MTX_PUBLISH_USER/PASS, SRT_PASSPHRASE, TZ
vps/mediamtx.yml              # ingest auth, HLS settings
front/                        # Svelte 5 + Vite static SPA
  package.json, package-lock.json, vite.config.js   # deps pinned: svelte, vite, hls.js
  Dockerfile                  # multi-stage: node:22-alpine build → caddy:2-alpine serve
  Caddyfile
  index.html, src/App.svelte, src/Player.svelte, src/Gallery.svelte, src/app.css
  public/img/*, public/favicon.ico, public/robots.txt
photod/photod.py, Dockerfile, requirements.txt, testdata/
pi/setup.sh                   # idempotent SSH provisioning
pi/mediamtx.yml.tpl           # rpiCamera + push (both transport variants)
pi/frogwatch-cam.service      # systemd unit
tools/mock-publish.sh         # ffmpeg testsrc publisher
README.md, CLAUDE.md          # rewritten (WireGuard section carries over)
```

Pin one MediaMTX version everywhere (latest stable 1.x at implementation time; Pi `linux_armv7` release asset + matching Docker tag; upgrade in lockstep — auth schema/rpiCamera params drift across minors).

## Key configs

### Pi `pi/mediamtx.yml.tpl` (rendered by envsubst from `/etc/frogwatch/frogwatch.env`, chmod 600)
- Disable api/metrics/hls/webrtc/srt/rtmp; RTSP on :8554 (localhost relay source + WG debugging).
- Path `cam`: `source: rpiCamera`, 1280x720@25 (720p uses full-FoV binned mode on Camera V2; 1080p would crop), `rpiCameraBitrate: 2000000`, `rpiCameraIDRPeriod: 50` (keyframe/2s = 1 HLS segment).
- `runOnReady` (SRT primary):
  `ffmpeg -rtsp_transport tcp -i rtsp://localhost:8554/cam -c copy -f mpegts "srt://${VPS_HOST}:8890?streamid=publish:frog&passphrase=${SRT_PASSPHRASE}&pkt_size=1316"`
  Fallback variant (PUSH_MODE var): `-f rtsp rtsp://${USER}:${PASS}@${VPS_HOST}:8554/frog`. `runOnReadyRestart: yes`.

### VPS `vps/mediamtx.yml`
- SRT :8890, RTSP :8554 (internal + fallback ingest), HLS :8888 with `hlsVariant: fmp4` (classic, not LL — robust through proxies), `hlsSegmentDuration: 2s`, `hlsSegmentCount: 7` (~6–10s latency).
- `authInternalUsers`: anonymous read-only; publisher user publish-only on path `frog`. Path `frog`: `srtPublishPassphrase` (10–64 chars — libsrt allows up to 79 but the Pi's ffmpeg 4.3 `-passphrase` option caps at 64; stay ≤64). **Correction:** MediaMTX does NOT expand `${VAR}` inside the yml; secrets are injected via its `MTX_*` env-override mechanism instead (`MTX_PATHS_FROG_SRTPUBLISHPASSPHRASE`, `MTX_AUTHINTERNALUSERS_1_USER/_PASS`) — still just Coolify env vars, no templating on VPS.

### `docker-compose.yml`
- `mediamtx`: pinned image, `restart: always`, `ports: ["8890:8890/udp"]`, config mounted ro, wget healthcheck on :8888.
- `front`: build ./front, mounts `photos` volume ro, `/healthz` healthcheck.
- `photod`: build ./photod, env `TZ=Europe/Berlin, RTSP_URL=rtsp://mediamtx:8554/frog, DAYLIGHT_START=08:00, DAYLIGHT_END=20:00, SAMPLE_INTERVAL_MIN=10`, mounts `photos` rw.
- Coolify: domain only on `front` (https://frogwatch.jan-berndt.de → 80); env vars runtime-available; **open 8890/udp in VPS/cloud firewall** (Traefik irrelevant for UDP).

### `front/Caddyfile`
```
:80 {
	handle /healthz { respond "OK" 200 }
	handle_path /stream/* { reverse_proxy mediamtx:8888 { flush_interval -1 } }
	handle_path /photos/* { root * /photos
		header Cache-Control "public, max-age=300"
		file_server }
	handle { root * /srv
		file_server }
}
```
`handle_path` strips prefix; `flush_interval -1` disables buffering for segment delivery. HLS URL public: `/stream/frog/index.m3u8` (manifest segment URLs relative → prefix proxy just works).

## photod (~150-line single file, Pillow+numpy — no opencv, frame grab via ffmpeg binary)

Loop: every `SAMPLE_INTERVAL_MIN` during daylight window → `ffmpeg -rtsp_transport tcp -i $RTSP_URL -frames:v 1 -q:v 2 /tmp/frame.jpg` (30s timeout; fails fast when no publisher → skip). Score, replace candidate if better (atomic tmp+rename on volume — survives restarts).

**Scoring:** downscale to 640px, PIL HSV → numpy. Frog mask = bright saturated red `(H<10|H>245)&(S>100)&(V>90)` OR blue `(150<H<190)&...`; `color_score = red_frac + blue_frac`. Sharpness = numpy-slicing Laplacian variance, used only as blur gate (`MIN_SHARPNESS`), not competing with color. `total = color_score`.

**Rollover:** `finalize_if_stale` at loop top: candidate date < today → `os.replace` to `/photos/<date>.jpg`, regenerate `index.json` by globbing `/photos/????-??-??.jpg` (self-healing). Works after any-length downtime. Day with no candidate → date absent, acceptable.

**CLI test mode:** `python photod.py --score img...` prints per-file scores — threshold calibration against `testdata/` + real frames.

## Pi `pi/setup.sh` (idempotent, run: `ssh raspi 'sudo bash -s' < pi/setup.sh` with tpl/unit scp'd)

1. Preflight: root, armv7l check.
2. Legacy camera stack must be OFF (`raspi-config nonint`; may require one reboot — script detects/reports). Verify `libcamera-hello --list-cameras` shows imx219. (mediamtx uses embedded libcamera; only legacy-stack-off matters.)
3. `apt-get install -y ffmpeg` (already installed during pre-check 2026-07-06); probe `ffmpeg -protocols | grep srt` → set PUSH_MODE (srt|rtsp) for template render. Probe already passed on the real Pi, so expect PUSH_MODE=srt; the check stays for idempotence.
4. Download pinned `mediamtx_vX.Y.Z_linux_armv7.tar.gz`, sha256 verify, install to `/opt/mediamtx/<ver>`, symlink `current` (rollback = re-point).
5. Write `/etc/frogwatch/frogwatch.env` (600) if absent (VPS_HOST, SRT_PASSPHRASE, creds); envsubst config.
6. **Stop+purge old app first** (camera exclusive): `supervisorctl stop frogwatch`, rm conf, `apt purge supervisor`.
7. Install `frogwatch-cam.service`: `Restart=always`, `RestartSec=5`, `StartLimitIntervalSec=0`, `User=pi`, `SupplementaryGroups=video`, `After=network-online.target`; `enable --now`.
8. Hardware watchdog: `/etc/systemd/system.conf.d/10-watchdog.conf` `RuntimeWatchdogSec=15` (bcm2835_wdt) — reboots Pi if kernel/PID1 hangs.
9. Self-check: `systemctl is-active` + `ffprobe rtsp://localhost:8554/cam`, PASS/FAIL summary.
- Script never touches `/etc/wireguard`.

## Frontend — Svelte 5 + Vite (user request: framework, simple/lightweight/fast)

Rationale: Svelte compiles to vanilla JS, ~5KB runtime, no virtual DOM — lightest mainstream framework; single static bundle served by caddy, no SSR/Node at runtime. All deps pinned via committed `package-lock.json`; hls.js as npm dep (no CDN).

- `front/Dockerfile` multi-stage: `node:22-alpine` → `npm ci && npm run build` → copy `dist/` into `caddy:2-alpine` `/srv` with `Caddyfile`.
- `Player.svelte`: `<video controls muted playsinline>`; Safari native HLS via `canPlayType`, else `import Hls from 'hls.js'`. Self-healing: fatal NETWORK_ERROR → `startLoad()` retry w/ backoff; MEDIA_ERROR → `recoverMediaError()`; else destroy+re-init after 10s; "Stream offline – reconnecting…" overlay state.
- `Gallery.svelte`: `onMount` fetch `/photos/index.json`, lazy `<img>` grid (`repeat(auto-fill, minmax(160px,1fr))`), date captions, newest first; hide section on 404/error.
- `App.svelte` + `app.css`: carry over dark-green branding, logo header, Impressum/Datenschutz footer from old site.
- Local dev: `npm run dev` with Vite proxy for `/stream` + `/photos` → local compose stack.

## Cutover order (simple — work on `main`, downtime during migration is fine)

1. Build everything directly on `main`. Site may serve the old version or nothing meanwhile — acceptable.
2. Local e2e: `docker compose -f docker-compose.yml -f docker-compose.local.yml up --build` + `tools/mock-publish.sh` (ffmpeg testsrc2 → SRT publish). Verify player :8080, photod grab (interval=1min), forced rollover (backdate candidate.json).
3. Delete old Coolify resource; create new one from `main` with the real domain (https://frogwatch.jan-berndt.de). Open 8890/udp firewall. Run mock-publish from laptop against VPS — validates public UDP path before touching Pi.
4. Pi cutover over WG SSH: env file → `setup.sh` (stops old app, starts mediamtx). Verify VPS logs `publishing to path 'frog'`, stream live on the domain. Calibrate photod thresholds with real frames.
5. Robustness drills: `ssh raspi sudo reboot` (stream self-returns ~60–90s); docker restart mediamtx (Pi pusher reconnects via runOnReadyRestart); restart photod (candidate survives).

## Verification

| What | Command | Expect |
|---|---|---|
| Pi service | `ssh raspi systemctl is-active frogwatch-cam` | active |
| Camera→RTSP | `ffprobe rtsp://10.8.0.2:8554/cam` (on WG) | h264 1280x720@25 |
| VPS ingest | mediamtx container logs | `is publishing to path 'frog'` |
| HLS | `curl -fsS https://frogwatch.jan-berndt.de/stream/frog/index.m3u8` | m3u8 |
| Site | `curl -fsS https://frogwatch.jan-berndt.de/healthz` | OK |
| photod score | `docker compose run --rm photod python photod.py --score testdata/*.jpg` | frog > empty; blurry rejected |
| Gallery | `curl -fsS .../photos/index.json` | JSON array |

## Risks

1. ~~**Bullseye ffmpeg SRT**~~ — **resolved 2026-07-06**: verified on the real Pi (protocol listed in+out, `-passphrase` option present, ffmpeg 4.3.9 + libsrt1.4-gnutls installed). setup.sh probe + RTSP/TCP fallback stay in as cheap insurance only.
2. Camera exclusivity: old picamera2 app must stop before mediamtx starts (script ordering). Legacy stack off may need one reboot.
3. MediaMTX config schema drift across 1.x — pin same version Pi+VPS, validate yml against that version's docs.
4. Coolify: env vars must be runtime; cloud-provider firewall separate from ufw for 8890/udp.
5. Bandwidth: if parents' upload stutters, drop bitrate to 1.5M / 20fps (one-line config + service restart).
6. photod HSV thresholds need real-frame calibration (`--score` CLI, 10-min loop during cutover).
