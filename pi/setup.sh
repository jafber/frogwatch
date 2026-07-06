#!/bin/bash
# Frogwatch Pi provisioning — idempotent, safe to re-run.
# Run on the Pi:            sudo bash setup.sh
# Or from a laptop over WG: ssh raspi 'sudo bash -s' < pi/setup.sh
#
# Reads /etc/frogwatch/frogwatch.env (creates a skeleton on first run).
# Never touches /etc/wireguard.
set -euo pipefail

MEDIAMTX_VERSION=v1.19.2
MEDIAMTX_SHA256=de0afed5ba33df231a6c3321207b4a906f1da9be7ce8b3efac008928e982ca6d
REPO_RAW=https://raw.githubusercontent.com/jafber/frogwatch/main

ENV_FILE=/etc/frogwatch/frogwatch.env
CONFIG=/etc/frogwatch/mediamtx.yml
UNIT=/etc/systemd/system/frogwatch-cam.service
REBOOT_REQUIRED=0

log()  { echo "[setup] $*"; }
fail() { echo "[setup] FAIL: $*" >&2; exit 1; }

# ---------- 1. preflight ----------
[ "$(id -u)" -eq 0 ] || fail "run as root (sudo)"
[ "$(uname -m)" = "armv7l" ] || fail "expected armv7l, got $(uname -m)"

# ---------- 2. legacy camera stack must be OFF ----------
if raspi-config nonint get_legacy | grep -q '^0$'; then
    log "legacy camera stack is ON -> disabling (needs one reboot)"
    raspi-config nonint do_legacy 1
    REBOOT_REQUIRED=1
else
    log "legacy camera stack is off"
fi
if [ "$REBOOT_REQUIRED" -eq 0 ]; then
    if libcamera-hello --list-cameras 2>/dev/null | grep -qi imx; then
        log "camera detected: $(libcamera-hello --list-cameras 2>/dev/null | grep -i imx | head -1)"
    else
        log "WARNING: libcamera-hello did not list a camera; continuing anyway"
    fi
fi

# ---------- 3. packages + SRT probe ----------
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ffmpeg gettext-base curl >/dev/null
if ffmpeg -hide_banner -protocols 2>/dev/null | grep -qw srt; then
    DETECTED_PUSH_MODE=srt
else
    DETECTED_PUSH_MODE=rtsp
fi
log "ffmpeg push transport: $DETECTED_PUSH_MODE"

# ---------- 4. install pinned mediamtx ----------
INSTALL_DIR=/opt/mediamtx/$MEDIAMTX_VERSION
if [ ! -x "$INSTALL_DIR/mediamtx" ]; then
    log "downloading mediamtx $MEDIAMTX_VERSION"
    TARBALL=/tmp/mediamtx_${MEDIAMTX_VERSION}_linux_armv7.tar.gz
    curl -fsSL -o "$TARBALL" \
        "https://github.com/bluenviron/mediamtx/releases/download/$MEDIAMTX_VERSION/mediamtx_${MEDIAMTX_VERSION}_linux_armv7.tar.gz"
    echo "$MEDIAMTX_SHA256  $TARBALL" | sha256sum -c - >/dev/null || fail "mediamtx checksum mismatch"
    mkdir -p "$INSTALL_DIR"
    tar -xzf "$TARBALL" -C "$INSTALL_DIR" mediamtx
    rm -f "$TARBALL"
else
    log "mediamtx $MEDIAMTX_VERSION already installed"
fi
ln -sfn "$INSTALL_DIR" /opt/mediamtx/current

# ---------- 5. env file ----------
mkdir -p /etc/frogwatch
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<'EOF'
# Frogwatch Pi secrets — fill in, then re-run setup.sh. Keep in sync with the
# VPS (Coolify env vars). Values must stay URL-safe (alphanumeric, - and _).
VPS_HOST=frogwatch.jan-berndt.de
MTX_PUBLISH_USER=frogpublisher
MTX_PUBLISH_PASS=
SRT_PASSPHRASE=
# auto = use SRT if ffmpeg supports it, else RTSP. Or force: srt | rtsp
PUSH_MODE=auto
EOF
    chmod 600 "$ENV_FILE"
    fail "created $ENV_FILE skeleton — fill in the secrets and re-run"
fi
chmod 600 "$ENV_FILE"
# read KEY=VALUE without sourcing (values must never hit the shell)
getvar() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -1; }
VPS_HOST=$(getvar VPS_HOST)
MTX_PUBLISH_USER=$(getvar MTX_PUBLISH_USER)
MTX_PUBLISH_PASS=$(getvar MTX_PUBLISH_PASS)
SRT_PASSPHRASE=$(getvar SRT_PASSPHRASE)
PUSH_MODE=$(getvar PUSH_MODE)
[[ "$VPS_HOST" =~ ^[A-Za-z0-9._-]+$ ]] || fail "VPS_HOST missing/invalid in $ENV_FILE"
for var in MTX_PUBLISH_USER MTX_PUBLISH_PASS SRT_PASSPHRASE; do
    [[ "${!var}" =~ ^[A-Za-z0-9_-]+$ ]] || \
        fail "$var must be non-empty and URL-safe ([A-Za-z0-9_-]) in $ENV_FILE — it is embedded in stream URLs"
done
PASSLEN=${#SRT_PASSPHRASE}
{ [ "$PASSLEN" -ge 10 ] && [ "$PASSLEN" -le 64 ]; } || fail "SRT_PASSPHRASE must be 10-64 chars"
[ "${PUSH_MODE:-auto}" = "auto" ] && PUSH_MODE=$DETECTED_PUSH_MODE
log "push mode: $PUSH_MODE"

# ---------- 6. render mediamtx config ----------
TPL=/tmp/frogwatch-mediamtx.yml.tpl
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-/nonexistent}")" 2>/dev/null && pwd || true)
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/mediamtx.yml.tpl" ]; then
    cp "$SCRIPT_DIR/mediamtx.yml.tpl" "$TPL"
else
    curl -fsSL -o "$TPL" "$REPO_RAW/pi/mediamtx.yml.tpl"
fi
if [ "$PUSH_MODE" = "srt" ]; then
    RUN_ON_READY="ffmpeg -hide_banner -loglevel warning -rtsp_transport tcp -i rtsp://localhost:8554/cam -c copy -f mpegts \"srt://$VPS_HOST:8890?streamid=publish:frog:$MTX_PUBLISH_USER:$MTX_PUBLISH_PASS&passphrase=$SRT_PASSPHRASE&pkt_size=1316\""
else
    RUN_ON_READY="ffmpeg -hide_banner -loglevel warning -rtsp_transport tcp -i rtsp://localhost:8554/cam -c copy -f rtsp rtsp://$MTX_PUBLISH_USER:$MTX_PUBLISH_PASS@$VPS_HOST:8554/frog"
fi
export RUN_ON_READY
envsubst '$RUN_ON_READY' < "$TPL" > "$CONFIG"
chown root:pi "$CONFIG"
chmod 640 "$CONFIG"
rm -f "$TPL"
log "rendered $CONFIG"

# ---------- 7. stop + purge old picamera2 app (camera is exclusive) ----------
if command -v supervisorctl >/dev/null 2>&1; then
    supervisorctl stop frogwatch >/dev/null 2>&1 || true
    rm -f /etc/supervisor/conf.d/frogwatch.conf
    log "purging old supervisor app"
    apt-get purge -y -qq supervisor >/dev/null 2>&1 || true
fi

# ---------- 8. systemd unit ----------
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/frogwatch-cam.service" ]; then
    cp "$SCRIPT_DIR/frogwatch-cam.service" "$UNIT"
else
    curl -fsSL -o "$UNIT" "$REPO_RAW/pi/frogwatch-cam.service"
fi
systemctl daemon-reload
systemctl enable frogwatch-cam.service >/dev/null 2>&1

# ---------- 9. hardware watchdog (bcm2835_wdt): reboot if kernel/PID1 hangs ----------
mkdir -p /etc/systemd/system.conf.d
cat > /etc/systemd/system.conf.d/10-watchdog.conf <<'EOF'
[Manager]
RuntimeWatchdogSec=15
EOF
log "hardware watchdog configured (active after next reboot/daemon-reexec)"

# ---------- 10. start + self-check ----------
if [ "$REBOOT_REQUIRED" -eq 1 ]; then
    log "REBOOT REQUIRED to finish disabling the legacy camera stack."
    log "run: sudo reboot  — the service starts automatically afterwards; re-run setup.sh to self-check"
    exit 0
fi

systemctl restart frogwatch-cam.service
sleep 8
PASS=1
if systemctl is-active --quiet frogwatch-cam.service; then
    log "service: active"
else
    log "service: NOT active"; PASS=0
fi
if timeout 20 ffprobe -v error -rtsp_transport tcp \
        -show_entries stream=codec_name,width,height -of csv=p=0 \
        rtsp://localhost:8554/cam 2>/dev/null | grep -q h264; then
    log "camera stream: h264 OK"
else
    log "camera stream: ffprobe FAILED (journalctl -u frogwatch-cam)"; PASS=0
fi
if [ "$PASS" -eq 1 ]; then log "PASS — all checks green"; else fail "self-check failed"; fi
