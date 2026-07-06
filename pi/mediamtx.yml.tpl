# MediaMTX config for the Pi, rendered by pi/setup.sh (envsubst).
# Do not edit /etc/frogwatch/mediamtx.yml directly; edit the template or
# /etc/frogwatch/frogwatch.env and re-run setup.sh.

logLevel: info

api: no
metrics: no
pprof: no
playback: no
rtmp: no
hls: no
webrtc: no
srt: no
moq: no

# local relay source + debugging over WireGuard (ffprobe rtsp://10.8.0.2:8554/cam)
rtsp: yes
rtspAddress: :8554
rtspTransports: [tcp]
rtspEncryption: "no"

paths:
  cam:
    source: rpiCamera
    # pin the 2x2-binned full-sensor mode; without this libcamera picks the
    # 1920x1080 sensor mode, which is a center crop (narrow FoV).
    # 4:3 output keeps the full field of view, like the old app's stills.
    rpiCameraMode: 1640:1232:10:P
    rpiCameraWidth: 1280
    rpiCameraHeight: 960
    rpiCameraFPS: 25
    rpiCameraBitrate: 2000000
    # keyframe every 2s = one HLS segment on the VPS
    rpiCameraIDRPeriod: 50
    runOnReady: ${RUN_ON_READY}
    runOnReadyRestart: yes
