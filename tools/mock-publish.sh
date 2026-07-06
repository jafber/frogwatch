#!/bin/bash
# Publishes a synthetic test pattern to the frogwatch SRT ingest.
# Usage:   tools/mock-publish.sh [HOST]          (default: localhost)
# Reads MTX_PUBLISH_USER/PASS + SRT_PASSPHRASE from secret.env (or $SECRET_FILE).
# Needs a local ffmpeg with SRT support (scoop install ffmpeg); if none is
# found, falls back to running ffmpeg in docker on the compose network.
set -euo pipefail
cd "$(dirname "$0")/.."

HOST=${1:-localhost}
ENV_FILE=${SECRET_FILE:-secret.env}
[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE (cp .env.example secret.env)"; exit 1; }

# read KEY=VALUE without sourcing (values must never hit the shell)
getvar() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -1; }
MTX_PUBLISH_USER=$(getvar MTX_PUBLISH_USER)
MTX_PUBLISH_PASS=$(getvar MTX_PUBLISH_PASS)
SRT_PASSPHRASE=$(getvar SRT_PASSPHRASE)
for var in MTX_PUBLISH_USER MTX_PUBLISH_PASS SRT_PASSPHRASE; do
    [[ "${!var}" =~ ^[A-Za-z0-9_-]+$ ]] || {
        echo "$var must be non-empty and URL-safe ([A-Za-z0-9_-]) — it is embedded in stream URLs"; exit 1; }
done

URL="srt://$HOST:8890?streamid=publish:frog:$MTX_PUBLISH_USER:$MTX_PUBLISH_PASS&passphrase=$SRT_PASSPHRASE&pkt_size=1316"
ARGS=(-re -f lavfi -i "testsrc2=size=1280x720:rate=25"
    -c:v libx264 -preset ultrafast -tune zerolatency -b:v 1M -g 50 -pix_fmt yuv420p
    -f mpegts "$URL")

if command -v ffmpeg >/dev/null && ffmpeg -hide_banner -protocols 2>/dev/null | grep -qw srt; then
    exec ffmpeg "${ARGS[@]}"
fi

echo "no local ffmpeg with SRT; using docker (compose network, host 'mediamtx')"
URL="srt://mediamtx:8890?streamid=publish:frog:$MTX_PUBLISH_USER:$MTX_PUBLISH_PASS&passphrase=$SRT_PASSPHRASE&pkt_size=1316"
ARGS[${#ARGS[@]}-1]="$URL"
NETWORK=$(docker network ls --format '{{.Name}}' | grep '_default$' | grep -i frogwatch | head -1)
exec docker run --rm --network "$NETWORK" linuxserver/ffmpeg "${ARGS[@]}"
