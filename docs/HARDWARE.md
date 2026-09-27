# Wiring, first power-up and economics

Use Pi USB to webcam and Pi USB to the ESP32-S3 UART bridge. ESP32 GPIO5/6 are servo signal outputs. All signal grounds join at a low-impedance common point; keep motor and servo high-current returns out of the logic-ground path. Do not join independent5V supply positives. Check the specific ESP32 board schematic and servo logic-high requirements; add a proper level translator if the servo does not accept3.3V signals.

1. Lift/immobilize the rover, disconnect drive power, detach servo horns and support the camera.
2. Verify regulator polarity/voltage and cable clearances. Size BEC using both servos' stall currents with margin; their current is unknown until exact models are supplied.
3. Flash ESP32 through UART bridge. Start host. Confirm **ESP32 acknowledged** before enable. No autonomous scanning occurs.
4. Enable manual at1500/1500, stop, remove servo power and fit horns near mechanical center. Reapply with bracket supported.
5. Enable manual and test small slider movements. Stop before changing reverse/limits. Reduce travel to clear all hard stops and cables. Change limits with conservative pulse bounds.
6. Verify pan/tilt tracking direction at low gain; if motion increases image error, stop immediately and reverse the affected axis.
7. Test GPIO7-to-ground STOP, pull USB, close browser, cover/disconnect camera. Verify motion stops and never resumes until explicit enable.
8. Run30min while checking Pi thermal throttling, supply drops and servo temperature. Then evaluate while rover stationary before any low-speed driving test.

## Bill of materials (prices intentionally not quoted)

| Item | Quantity | Selection constraint |
|---|---:|---|
| Pi4B4GB + storage + supply + cooling | 1 | Existing board preferred; inference benchmark required |
| ESP32-S3 DevKit with UART bridge | 1 | Pin/board variant verified before flashing |
| USB UVC webcam | 1 | Reuse existing Redragon if UVC-compatible |
| Positional hobby servo | 2 | Match load torque, voltage, pulse range; no continuous-rotation servos |
| Pan/tilt bracket/support | 1 | Low backlash, camera CG near tilt axis |
| Servo BEC, fuse, wiring and disconnect | 1 set | Combined stall current, appropriate wire gauge |
| STOP/HOLD switch | 1 optional | GPIO7 to GND, normally open; software stop only |

Dominant new cost is Pi/camera if not already owned; with those reused, suitable servos/bracket and reliable power dominate. Frugal route: use existing Pi4/webcam, small balanced bracket and slower subject motion, then benchmark NCNN before buying Pi5/accelerator. Do not purchase an accelerator for this MVP. A more expensive Pi cannot correct mechanical backlash or an undersized servo supply.

ArduRover controller, motor drivers and RC receiver stay independent. Do not connect ESP32 servo signals to the autopilot's outputs. Future MAVLink should begin read-only and use a dedicated verified port; integration needs arbitration, pilot takeover and stale-attitude tests before it can control a mount.
