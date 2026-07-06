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
    # 720p = full-FoV binned mode on the Camera V2; 1080p would crop
    rpiCameraWidth: 1280
    rpiCameraHeight: 720
    rpiCameraFPS: 25
    rpiCameraBitrate: 2000000
    # keyframe every 2s = one HLS segment on the VPS
    rpiCameraIDRPeriod: 50
    runOnReady: ${RUN_ON_READY}
    runOnReadyRestart: yes
