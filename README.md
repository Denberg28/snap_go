# Snap_Go · 0.3.0

Android operator app source and APK build instructions: [`android/README.md`](android/README.md). It uses the existing Pi dashboard and control lease; the Pi remains the only ESP32 controller.

Android 0.3.0 adds **LIVE / TEST** tabs. TEST opens a bundled offline sample scene for virtual pan, tilt and synthetic person/ball detections. It does not connect to the Pi or drive physical servos. LIVE uses the Pi webcam, YOLO model and ESP32 with explicit enable. Switching out of LIVE requests STOP and a return to LIVE requires reconnection and another explicit enable.

The 0.3.0 control layout places a pan joystick left of the camera and a tilt joystick right of it. Both return to neutral on release and request HOLD. Open **Settings** to connect, choose calibration limits and tracking class. The APK displays the dashboard served by the Pi, so install the matching 0.3.0 Pi software to see this layout.

Local, two-servo webcam pan/tilt tracking for a rover: **USB webcam → Raspberry Pi 4B (YOLOv8n) → USB serial → ESP32-S3 → pan + tilt servos**.

Private bench-testing candidate. Simulation and hardware-independent tests are available; read `docs/VERIFICATION.md` for actual results. Hardware qualification is required before mounting on a moving rover. Repository destination: https://github.com/denberg28/snap_go (public; publication pending owner confirmation).

## Quick start: no hardware

Python 3.10–3.12; Linux is the primary supported host.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m snap_go.app --simulate
```

Open http://127.0.0.1:8080 and paste the access token printed by the service. Select **Manual positioning**, enable, move either slider, then **STOP / HOLD**. Select **Track subject**, enable, and use simulation faults to check target/link loss. Simulation never opens a camera or serial port and is prominently labeled.

The mount defaults disabled. **Keep the dashboard visible while controlling**: hiding it requests stop; closing it or losing contact expires its 1-second control lease. Reopening a tab never resumes motion automatically. Settings persist; enabled state does not.

## Raspberry Pi setup

Use Raspberry Pi OS 64-bit with Python 3.11 (Bookworm is the reference target); Python 3.13 is not yet supported by this pinned environment. The Pi 4B 4GB is the baseline. The same host interface supports a later Pi 5; benchmark both on actual hardware. No promised FPS until measured.

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential libgl1 libglib2.0-0 v4l-utils
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[vision]'
mkdir -p models
# One-time, explicit model provisioning (requires Internet):
python scripts/provision_model.py
python scripts/doctor.py
ls -l /dev/serial/by-id/
python -m snap_go.app --serial /dev/serial/by-id/YOUR_ESP32 --model models/yolov8n.pt
```

`uv.lock` records the resolved dependency versions and hashes; use `uv sync --frozen --extra vision` for the fully resolved environment. Ordinary pip uses direct dependency pins but can resolve newer transitive dependencies. Model provisioning records SHA-256 in `models/SHA256SUMS`. Keep that file with your provisioned weights. Only load trusted weights. The run command refuses missing model files and never provisions them silently.

For a phone dashboard, start with `--host 0.0.0.0` on a trusted isolated LAN and visit `http://PI_IP:8080`. All API requests (including images) require the token. HTTP is not encrypted: for untrusted networks use an SSH tunnel, keep the localhost bind, and do not port-forward this service to the Internet. No cloud API, account, or paid service is required. `.env.example` is documentation; it is not automatically sourced by the CLI.

## ESP32-S3 firmware

```bash
python -m pip install platformio==6.1.18
python -m platformio run -d firmware
python -m platformio run -d firmware -t upload --upload-port /dev/ttyUSB0
```

Reference board: **ESP32-S3-DevKitC-1** with its **USB-to-UART** connector (UART0). Native USB CDC is deliberately disabled. On a dual-port board use the UART connector, not the native USB/OTG connector. A board with native USB only needs a 3.3 V USB-UART adapter connected to UART0 GPIO43 TX / GPIO44 RX, with common ground; do not connect 5 V logic. Exact board variant/connector labels must be checked before flashing. Do not open Arduino Serial Monitor while Snap_Go is connected.

| ESP32-S3 | Connection |
|---|---|
| GPIO5 | Pan servo signal |
| GPIO6 | Tilt servo signal |
| GPIO7 | Optional normally-open STOP/HOLD switch to GND |
| GND | Servo BEC negative/common ground |
| USB-to-UART port | Raspberry Pi USB |

Supply servos from a **separate regulated BEC matched to their voltage and combined stall current**. Never power the servos from the ESP32's 3.3 V pin or the Pi's GPIO supply. Avoid backfeeding between BEC and USB rails. GPIO7 is a software stop input, not a safety-rated emergency stop; it holds PWM at the last position. Fit an accessible power disconnect for bench testing. See `docs/HARDWARE.md`.

## ArduRover compatibility

v0.3.0 is an **independent camera payload**. It does not send MAVLink, change ArduRover parameters, claim a flight-controller serial port, arm/disarm the rover, or control driving. The two servo signals connect only to the ESP32; do not wire a flight-controller PWM output onto the same signals. This works alongside an ArduRover vehicle without depending on its firmware version. It is **not yet a MAVLink gimbal device** and has no attitude stabilization, RC takeover, or mission ROI support. These are explicit future integration work, not hidden prerequisites.

## Tracking behavior

Default subject is COCO class 0 (person), confidence 0.5, inference size 320, webcam request 640×480. Select another COCO class ID in calibration while disabled. On enable, select the matching detection nearest image center; subsequently associate by nearest center within a normalized 0.25 gate. This is basic subject continuity, **not identity recognition**: crossing or occluded subjects can switch association. There is no face recognition or recording.

Proportional image-error control, deadband, reversed-axis options, software pulse limits, and slew limiting reduce chatter. It is camera-relative tracking, not world-frame stabilization. No detection immediately freezes the command. One second of target loss or a frame older than 0.75 seconds disables tracking. Inference/capture runs in a separate process so stalls cannot prevent the ESP32 timeout. The host sends at 20 Hz; firmware emits 50 Hz PWM and independently caps slew at 200 µs/s.

## Reliability and testing

```bash
python -m pip install '.[dev]'
python -m pytest -q
node --check snap_go/static/app.js
python scripts/check_versions.py
python -m build
```

Tests cover controller latches, limits, persistence, CRC corruption, fragmented streams, actual pseudoterminal serial transport, browser lease expiry, API validation/auth, and native C++ firmware guard behavior including timer/sequence wrap. Automated hardware build/check/release workflow is in `.github/workflows/ci.yml`.

`docs/SPEC.md`: acceptance criteria and assumptions. `docs/RELEASE.md`: installation, upgrade, rollback and publish procedure. `docs/CONTINUITY.md`: decisions, completed work and next steps. No application signing key is created; ESP32 secure-boot signing is not provisioned for this prototype.

## Dependency licensing

Ultralytics YOLO code/models use AGPL-3.0 or an enterprise license. This prototype's original source is provided under AGPL-3.0-only (see LICENSE and third-party notices); there is no paid dependency in the chosen path. Review the upstream terms before a proprietary product release. Source: https://docs.ultralytics.com/models/yolov8/ and https://www.ultralytics.com/license.

### Optional NCNN optimization

After a baseline measurement, install the `ncnn` extra and explicitly export on your provisioned machine:

```bash
python -m pip install '.[vision,ncnn]'
python -c "from ultralytics import YOLO; YOLO('models/yolov8n.pt').export(format='ncnn', imgsz=320)"
python -m snap_go.app --model models/yolov8n_ncnn_model --serial /dev/serial/by-id/YOUR_ESP32
```

Export may download its conversion tools; complete it before offline use. This alternative is not benchmarked or hardware-qualified in v0.3.0. It retains the same stale-frame deadline rather than weakening failsafes to hide slow inference.
