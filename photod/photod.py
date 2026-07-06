#!/usr/bin/env python3
"""photod: periodically grabs frames from the frog stream during daylight
and keeps the most frog-visible photo of each day in /photos.

Daily rollover publishes the best candidate as /photos/<date>.jpg and
regenerates /photos/index.json (a JSON array of date strings).
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

PHOTOS_DIR = Path(os.environ.get("PHOTOS_DIR", "/photos"))
RTSP_URL = os.environ.get("RTSP_URL", "rtsp://mediamtx:8554/frog")
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Berlin"))
DAYLIGHT_START = os.environ.get("DAYLIGHT_START", "08:00")
DAYLIGHT_END = os.environ.get("DAYLIGHT_END", "20:00")
SAMPLE_INTERVAL_MIN = float(os.environ.get("SAMPLE_INTERVAL_MIN", "10"))
MIN_SHARPNESS = float(os.environ.get("MIN_SHARPNESS", "30"))
GRAB_TIMEOUT_S = 30

CANDIDATE_JPG = PHOTOS_DIR / "candidate.jpg"
CANDIDATE_META = PHOTOS_DIR / "candidate.json"


def log(msg):
    print(f"{datetime.now(TZ).isoformat(timespec='seconds')} {msg}", flush=True)


def score_image(path):
    """Returns (color_score, sharpness). color_score = fraction of pixels
    that look like a bright saturated red or blue frog."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((640, 640))
    h, s, v = (np.asarray(b, dtype=np.int32) for b in img.convert("HSV").split())
    bright = (s > 100) & (v > 90)
    red = ((h < 10) | (h > 245)) & bright
    blue = (h > 150) & (h < 190) & bright
    color_score = red.mean() + blue.mean()

    g = np.asarray(img.convert("L"), dtype=np.float64)
    lap = (
        g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:] - 4 * g[1:-1, 1:-1]
    )
    return float(color_score), float(lap.var())


def grab_frame(dest):
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-rtsp_transport", "tcp", "-i", RTSP_URL,
        "-frames:v", "1", "-q:v", "2", "-y", str(dest),
    ]
    try:
        res = subprocess.run(cmd, timeout=GRAB_TIMEOUT_S, capture_output=True)
    except subprocess.TimeoutExpired:
        return False
    return res.returncode == 0 and dest.exists() and dest.stat().st_size > 0


def atomic_write_json(path, data):
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def read_candidate_meta():
    try:
        return json.loads(CANDIDATE_META.read_text())
    except (OSError, ValueError):
        return None


def regenerate_index():
    dates = sorted(p.stem for p in PHOTOS_DIR.glob("????-??-??.jpg"))
    atomic_write_json(PHOTOS_DIR / "index.json", dates)
    log(f"index.json regenerated ({len(dates)} photos)")


def finalize_if_stale(today_str):
    """Publish yesterday's (or older) candidate as its day's photo."""
    meta = read_candidate_meta()
    if meta is None or meta.get("date") == today_str:
        return
    if CANDIDATE_JPG.exists():
        os.replace(CANDIDATE_JPG, PHOTOS_DIR / f"{meta['date']}.jpg")
        log(f"finalized photo for {meta['date']} (score {meta.get('score', 0):.4f})")
    CANDIDATE_META.unlink(missing_ok=True)
    regenerate_index()


def in_daylight(now):
    hhmm = now.strftime("%H:%M")
    return DAYLIGHT_START <= hhmm < DAYLIGHT_END


def sample(now):
    frame = PHOTOS_DIR / "frame.tmp.jpg"
    if not grab_frame(frame):
        log("frame grab failed (no publisher?), skipping")
        return
    color, sharpness = score_image(frame)
    meta = read_candidate_meta()
    today_str = now.strftime("%Y-%m-%d")
    best = meta["score"] if meta and meta.get("date") == today_str else -1.0
    if sharpness < MIN_SHARPNESS:
        log(f"sample rejected: too blurry (sharpness {sharpness:.1f})")
    elif color <= best:
        log(f"sample kept old candidate (score {color:.4f} <= {best:.4f})")
    else:
        os.replace(frame, CANDIDATE_JPG)
        atomic_write_json(
            CANDIDATE_META,
            {"date": today_str, "score": color, "taken": now.isoformat(timespec="seconds")},
        )
        log(f"new candidate (score {color:.4f}, sharpness {sharpness:.1f})")
    frame.unlink(missing_ok=True)


def main_loop():
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    regenerate_index()
    log(f"photod started: {RTSP_URL}, window {DAYLIGHT_START}-{DAYLIGHT_END}, "
        f"every {SAMPLE_INTERVAL_MIN}min")
    while True:
        now = datetime.now(TZ)
        finalize_if_stale(now.strftime("%Y-%m-%d"))
        if in_daylight(now):
            sample(now)
        time.sleep(SAMPLE_INTERVAL_MIN * 60)


def score_cli(paths):
    print(f"{'file':40} {'color':>8} {'sharp':>8}  verdict")
    for p in paths:
        color, sharpness = score_image(p)
        verdict = "BLURRY" if sharpness < MIN_SHARPNESS else f"{color:.4f}"
        print(f"{Path(p).name:40} {color:8.4f} {sharpness:8.1f}  {verdict}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--score":
        score_cli(sys.argv[2:])
    else:
        main_loop()
