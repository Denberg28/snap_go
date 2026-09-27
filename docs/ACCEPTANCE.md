# MVP acceptance criteria

Software gates:
- All Python tests pass on Python 3.11+.
- Package builds as wheel/sdist.
- Corrupt serial packets are rejected using CRC32.
- Tracking begins disabled after restart.
- Stale target data cannot continue moving the mount.
- Manual and Center commands enable/hold servo output without enabling tracking.
- Explicit Release disables tracking and servo output.

Bench hardware gates (not yet verified):
- ESP32-S3 boots with servos detached until first valid command.
- Loss of Pi/USB commands for >500 ms detaches both servos.
- Pan/tilt commands never exceed configured hard limits.
- Webcam runs 30 minutes without process crash.
- Tracking maintains a person inside the central 20% window for 90% of a slow walking bench test at 2-4 m.
- Command-to-servo median latency <=150 ms; 95th percentile <=250 ms.
- No brownout/reset while both servos are commanded under representative load.
- ArduRover steering/throttle remains functional if Snap_Go is powered off or rebooted.
