# Recovery / failsafe sequence

1. Tracking starts OFF.
2. If the detector loses the subject, the Pi stops issuing position changes and holds the last safe angle.
3. If serial acknowledgement fails, the Pi reports the link error; do not auto-rearm tracking.
4. If the ESP32 receives no valid command for 500 ms, it detaches both servo outputs.
5. After any brownout, reboot, unplug, or unexpected motion: power the servo rail off, remove horns/load if needed, inspect wiring, restart the ESP32, verify Center at reduced travel, then re-enable tracking manually.
