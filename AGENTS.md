# AGENTS.md

Snap_Go is safety-adjacent rover camera hardware. Preserve these invariants:
- ArduRover propulsion/navigation remains independent of camera tracking.
- Tracking and servo-output enable are separate states.
- Tracking defaults OFF at boot.
- ESP32 owns a hardware-side serial watchdog and detaches servos on timeout.
- Clamp every commanded angle to calibration limits on both Pi and ESP32.
- Never commit credentials, Wi-Fi passwords, signing keys, or device secrets.
- Every behavioral change needs tests and a changelog note.
