# Changelog

## 0.2.0 - 2026-09-27
- Reworked the operator interface around a large, center-locked camera pane for landscape use.
- Added LIVE / TEST mode switching and a simulated moving or stationary detection target.
- Added compact pan and tilt joystick controls with center, tracking, and servo-release actions.
- Added live-stream configuration through `SNAP_GO_STREAM_URL` while retaining a safe test view when no stream is configured.
- Added direct access to the latest GitHub release from the Update control.
- Preserved tracking-off-at-boot, travel clamps, stale-target hold, and ESP32-S3 watchdog safety behavior.

## 0.1.0 - 2026-09-27
- Initial Raspberry Pi dashboard/core package.
- Two-axis tracking controller with deadband, step limiting, calibration and stale-target hold.
- ESP32-S3 pan/tilt firmware with angle clamps and 500 ms independent command timeout.
- Manual, center, tracking, and servo-release controls.
- Unit tests, CI, wiring, acceptance, and recovery documentation.
