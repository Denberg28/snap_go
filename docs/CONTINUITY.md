# Continuity — Snap_Go 0.1.0

## Current intent

User: Engr. Marlou T. Dy. Build a reliable two-servo webcam pan/tilt payload for ArduRover using Raspberry Pi4B4GB YOLOv8n and ESP32-S3. Destination `denberg28/snap_go`. New project; no old turret code copied. Independent pan+tilt is assumed. Existing webcam reuse preferred. No paid services.

## Repository/publication

GitHub metadata confirmed the destination exists, is empty and PUBLIC; connected account has admin/push access. No code, tags or release were pushed because public publication was not clearly authorized in the user's private-testing/public-release template. Local commit and tag plus Git bundle preserve source/history. Ask for public publication confirmation only after delivering the concrete testing package; alternatively the user can make the destination private. Do not imply GitHub Release exists.

## Completed

- Full specification, flow, measurable acceptance, assumptions, BOM without invented prices.
- Pi service, isolated latest-frame vision worker, YOLOv8n320 interface, guarded nearest-center association.
- Local token-protected dashboard, manual/track/stop, calibration persistence and error reporting.
- CRC/sequence/ACK serial transport; ESP32-S3 firmware with bounded parser, watchdog latch, narrow PWM limits, slew limits, optional GPIO7 STOP/HOLD.
- Simulation and deterministic tests; source/version/package tooling and release workflow.
- Installation, wiring, calibration, service deployment, upgrade and rollback instructions.
- Dependency audit findings addressed by updating torch/torchvision and setuptools; hashes in uv.lock. Exact results in VERIFICATION.md.

## Decisions to preserve

1. No rover driving, arming or autopilot parameter mutations. No direct MAVLink integration in this MVP.
2. Hardware defaults disabled. Recovery/serial reconnect/browser reopen never automatically re-enable.
3. STOP holds last commanded PWM; it is not torque release or a safety-rated stop. Reboot removes pulses.
4. USB UART bridge, not native USB CDC; hardware-specific board profile and pin assignments documented.
5. Local operation after explicit provisioning. No cloud video, recordings, face recognition, or hidden model download at startup.
6. No degree/pose claims without calibrated feedback. ACK is commanded PWM only.
7. Target association is basic nearest-center continuity; crossings/occlusion remain a limitation.

## Next milestone: bench qualification

Read VERIFICATION.md first. Complete any blocked firmware/UI build gate. On the user's actual Pi/ESP/webcam/servos verify board identity, camera UVC mode, regulator sizing and mechanical clearance. Measure pulses, link timeout, STOP, first-enable behavior, target loss and30-minute thermal/power stability. Measure inference FPS/age and tracking centering against SPEC.md. Compare NCNN320 if necessary, then stationary-rover test before slow driving. Ask for servo models and ESP32 board photo if hardware choices remain consequential. Only then call a version hardware-qualified.

Future (not implemented): MAVLink gimbal protocol, RC takeover, vehicle-motion interlock, attitude stabilization and stronger association. Do not silently expand scope or weaken stale-frame safety to mask poor performance.
