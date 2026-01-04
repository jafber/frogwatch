# Dockerfile for running raspi scripts on Raspberry Pi
FROM python:3.11-slim-bullseye

# Install system dependencies for picamera2 and RPi.GPIO
RUN apt-get update && \
    apt-get install -y libcamera-dev python3-picamera2 python3-rpi.gpio && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "__init__.py"]
