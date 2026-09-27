# Snap_Go

Snap_Go is a reliability-first two-axis subject-tracking camera module for an ArduRover platform. A Raspberry Pi 4B reads a USB webcam and performs object detection; an ESP32-S3 owns the pan/tilt servo outputs and enforces an independent command watchdog. The rover flight controller keeps responsibility for driving, steering, navigation and vehicle failsafes.

## MVP hardware

- Raspberry Pi 4B 4 GB (Pi 5 can replace it later)
- Redragon USB webcam
- ESP32-S3 DevKit
- Two 12 kg digital servos for pan + tilt
- Separate regulated 5-6 V servo power supply sized for both servo stall currents; **do not power the servos from the Pi or ESP32 5 V rail**
- USB serial between Pi and ESP32-S3 for the first release

## Safety / reliability behavior

1. Tracking starts disabled after every process/MCU restart.
2. The Pi only enables tracking after an explicit user command.
3. If detections become stale, the Pi stops changing the target position and holds the current camera angle; it does not chase the last known location.
4. If valid Pi commands stop for 500 ms, ESP32-S3 detaches both servo outputs independently.
5. Pan/tilt travel is clamped by saved calibration limits.
6. ArduRover remains electrically and logically independent of camera tracking in v0.1.

## Quick start on Raspberry Pi OS 64-bit

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e '.[vision]'
cp .env.example .env
snap-go
```

Open `http://<raspberry-pi-ip>:8080`. Calibrate with the servo horns/mechanics unloaded or disconnected first, then test at reduced travel before enabling tracking.

Ultralytics' Raspberry Pi guidance recommends NCNN for faster ARM inference. The initial MVP keeps the requested YOLOv8n model path but isolates the detector so a later NCNN model or newer nano model can be substituted without changing the servo safety layer.

## ESP32-S3 firmware

Firmware lives in `firmware/` and uses PlatformIO. Defaults are GPIO17 pan and GPIO18 tilt; change these in `firmware/platformio.ini` if they conflict with your exact board or wiring.

```bash
cd firmware
pio run
pio run -t upload
pio device monitor
```

## Verification status

Software unit tests cover protocol CRC, parser rejection, tracking limits/deadband/staleness, calibration persistence, and mocked serial acknowledgement. Hardware gates remain open until the actual webcam, ESP32-S3, servo power supply and pan/tilt mechanics are connected and measured.

See `docs/ACCEPTANCE.md`, `docs/WIRING.md`, and `docs/RECOVERY.md` before rover installation.
