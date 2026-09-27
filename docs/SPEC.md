# Specification and acceptance · 0.1.0

## Goal and user flow

An operator fits a webcam to a two-axis servo bracket, calibrates narrow travel limits, checks manual direction, selects a supported object class and enables local YOLOv8n tracking. The Pi detects; ESP32 owns PWM and last-command watchdog. The operator sees camera/link health, stops, fixes faults and explicitly enables again. Calibration survives restart; active control never does.

## Decisions and assumptions

- Two servos mean pan + tilt, not two mechanically linked pan actuators.
- Existing USB UVC webcam (including the user's Redragon if it enumerates as UVC); exact model/format unverified. No ESP32 camera required.
- Raspberry Pi 4B 4GB runs inference; ESP32-S3 never runs YOLO.
- ESP32-S3-DevKitC-1 / UART bridge, Arduino-ESP32 2.x through pinned PlatformIO espressif32 6.10.0. LEDC channel API is intentionally the 2.x API, not Arduino 3.x.
- Default pulse hard envelope 1100–1900 µs; narrower host travel: pan 1200–1800, tilt 1300–1700; 1500 centers. These are starting assumptions, not verified mechanical safe angles.
- Servo make, voltage, stall current, load, horn geometry and pulse-to-angle relationship unknown. No degree readout or torque guarantee. There is no physical position feedback; ACK reports commanded PWM, not measured angle.
- Independent payload compatibility with ArduRover; MAVLink gimbal integration excluded from MVP.
- One operator on a trusted local network; any authenticated browser is an operator. No arbitration among multiple operators.
- Private testing candidate; public repository publication requires explicit decision.

## MVP scope

Dashboard, manual sliders/center, tracking class/configuration, newest-frame capture, model/camera fault reporting, binary acknowledged serial link, CRC, sequence rejection, rate/pulse limits, host/firmware watchdogs, local STOP/HOLD, settings persistence, simulated fault injection, command-line diagnostics, build/test/package automation, upgrade/rollback instructions.

## Acceptance criteria

| Requirement | Criterion | Verification |
|---|---|---|
| Startup | No servo pulses until first valid explicit enable after disabled handshake | Native guard test; electrical measurement pending |
| Serial safety | No new motion command after 350 ms without a valid new packet; host detects ACK loss within 300 ms | Native/PTY tests; physical measurement pending |
| Recovery | Fault recovery alone never re-enables movement | Automated controller + firmware + API tests |
| Browser loss | Disabled after 1 s without lease; independent firmware fallback if host stalls | HTTP integration test; full hardware pending |
| Camera stale | Tracking disabled when last accepted capture is >0.75 s old | Controller test; real camera pending |
| Target loss | Hold immediately on no matching detection; disarm after 1 s | Tests; real crossing subjects pending |
| Limits | All commanded pulse targets remain within calibrated bounds and firmware 1100–1900 µs envelope | Unit/native tests; horn envelope pending |
| Slew | Host <=configured µs/s (default180); firmware <=200 µs/s | Tests; scope pending |
| Config | Invalid/nonfinite/out-of-range config rejected; valid save atomic and reloads disabled | Automated test |
| Interface | Desktop/mobile no horizontal overflow; manual/track/stop/config flows work | Browser test if runtime available |
| Performance | Bench target >=3 inference FPS at320; 95% capture-to-result <0.75 s on Pi4 | Not yet measured; reduce input load or use NCNN if unmet |
| Tracking | Static/slow subject stays within central20% of image for >=90% of a60s trial after acquisition | Bench test pending, not guaranteed |
| Endurance | 30-minute camera+servo bench run with zero unexplained resets or auto-rearms | Pending physical equipment |

## Control equations

For normalized detection center (x,y), e = 2(x−0.5), 2(y−0.5). Outside deadband, pulse change = sign × gain × e × dt, limited to ±speed×dt and calibrated bounds. Missing match sets e=0. dt is capped at0.1 s so delayed host ticks cannot catch up in one jump. Gain units are µs/s; conversion to degrees requires measured servo calibration.

## Failures and limitations

A powered hobby servo may move toward1500 µs on its first enabled pulse: initialize with horns detached. Stop holds torque, not power isolation. A board reset removes PWM; a gravity-loaded tilt can fall. Provide mechanical support. There is no independent safety-rated circuit. Nearest-center association may swap subjects. A camera driver may deliver buffered frames; capture-thread timestamps measure receipt, not sensor exposure. No rover speed interlock or stabilized horizon. Bounds cannot compensate for a loose horn, insufficient BEC, overloaded servo or electrical fault.
