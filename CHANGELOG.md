# Changelog

## 0.10.0 — 2026-09-27 — live operator + function servos

- Rebuilt the connected Live screen with the same fixed three-pane operator layout used by Test.
- Live center pane now displays the real Pi camera feed while retaining pan/tilt, tracking, centering, status and settings.
- Added F1/F2/F3 buttons at the far right of the bottom control pane in both Test and Live.
- Wired F1/F2/F3 through the Pi/serial protocol to ESP32-S3 GPIO 8/9/10 as independent 50 Hz servo outputs.
- Function outputs fail OFF on STOP, browser lease expiry, serial link loss, firmware watchdog timeout or STOP input.


## 0.9.0 — 2026-09-27 — light/dark theme candidate

- Added a compact sun/moon theme toggle beside the Live mode menu.
- Persisted the selected light or dark theme between app launches.
- Applied the theme to the native Android shell and Pi-hosted Live dashboard.
- Carried the saved appearance into Test mode without changing camera/tracking behavior.


## 0.8.0 — 2026-09-27 — compact navigation candidate

- Replaced the full-width Live / Test / Update tab strip with a compact upper-left mode menu.
- Reclaimed vertical space for the center preview by moving status badges into the camera pane.
- Reduced simulated person and detection-box scale so targets no longer dominate the frame.
- Kept navigation separate from the Manual/Track control row and retained the fixed, non-draggable preview.


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
