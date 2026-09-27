# Changelog

## 0.7.0 — 2026-09-27 — fixed operator UI candidate

- Locked the Android Test screen to a fixed viewport so the camera/control layout no longer drags or scrolls.
- Reworked the APK shell and Test screen with a cleaner TeleRC-inspired card/navigation treatment.
- Increased the usable center camera pane by narrowing the pan/tilt side controls and reducing vertical chrome.
- Kept joystick interaction isolated to the two side controls while the center preview is non-interactive and stable.
- Preserved moving/stationary target simulation, detection toggle, tracking, center, reset and update workflows.

## 0.6.0 — 2026-09-27 — bench-testing candidate

- Enlarged the landscape Test camera scene and compacted adjacent controls.
- Simulated bounded pan/tilt tracking that keeps a moving target near the center with a small deadband and displayed virtual error.

## 0.1.0 — 2026-09-27 — bench-testing candidate

- New Raspberry Pi YOLOv8n webcam worker with latest-frame capture and stale-result rejection.
- ESP32-S3 pan/tilt PWM with fixed binary CRC protocol, sequence checks, timeout latch, pulse/slew bounds and STOP/HOLD input.
- Local responsive dashboard: manual/track, diagnostics, settings, authenticated control and browser lease.
- Simulation fault injection, persisted calibration, tests, build/release workflow and deployment documentation.
- ArduRover-compatible independent camera payload; no MAVLink/RC/drive integration yet.
- Hardware qualification and public repository publication pending; see VERIFICATION.md.
