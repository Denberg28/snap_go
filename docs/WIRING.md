# Wiring

## Data
Pi USB host -> ESP32-S3 USB serial. Do not connect Snap_Go directly to ArduRover MAVLink for v0.1.

## Servo signal
Default firmware pins: GPIO17 = pan signal, GPIO18 = tilt signal. Verify the exact ESP32-S3 DevKit pinout before connecting.

## Power
Use a dedicated regulated 5-6 V servo supply/BEC sized from the actual servo datasheet and measured stall current. Connect servo supply ground, ESP32 ground, and Pi/USB ground at a common reference. Do not feed servo power into the Pi 5 V rail or ESP32 5 V rail.

Start with servo horns removed. Confirm neutral, direction, and limits before attaching mechanics.
