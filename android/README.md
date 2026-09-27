# Snap Go Android operator · 0.6.0

Version 0.6.0 enlarges the landscape scene and keeps a synthetic moving target near center when tracking. Version 0.5.0 opens TEST in landscape, keeps the Android status/navigation bars clear of controls, compacts the layout, and lets you freeze or animate the synthetic target. LIVE returns to portrait. The test target is simulated and cannot move real servos.

Android 8+ app for the Pi's existing dashboard. The phone communicates with the Pi over local Wi-Fi; the Pi alone communicates with the ESP32-S3 over USB. The app does not control ArduRover drive or arm state.

Version 0.3.0 added **LIVE / TEST** tabs. TEST runs a bundled offline virtual camera scene with sample person/ball detection boxes, manual pan/tilt joysticks and synthetic target following. It sends no requests and cannot move the actual mechanism. LIVE connects to the matching Pi 0.6.0 server, shows the webcam and runs actual YOLO tracking after operator enable. Switching to TEST requests STOP before removing the live screen; the Pi's control lease is the fallback if the request fails. Returning to LIVE requires reconnecting and enabling again.

The control view shows two touch joysticks around the camera feed on the matching Pi dashboard. Pan is left/right and tilt is up/down; release requests HOLD. Settings contains the Pi token, mount calibration, and tracking configuration. The native **Pi connection** button changes the server address. The app reads the dashboard from the Pi, so update the Pi installation alongside the APK.

## Install and connect

Build with JDK 17 and Android SDK 35: `cd android && gradle assembleDebug`. Install `app/build/outputs/apk/debug/app-debug.apk`. CI also builds a debug APK artifact when this project is pushed to the configured repository. Debug APKs are for private testing and are signed with Android's generated debug key; there is no production signing key in source.

Start the Pi service with `python -m snap_go.app --host 0.0.0.0 --serial /dev/serial/by-id/YOUR_ESP32 --model models/yolov8n.pt`. Connect phone and Pi to the same trusted Wi-Fi. Enter `http://PI_PRIVATE_IP:8080` in the app and enter the Pi's access token in the dashboard. Pi addresses under 10/8, 172.16/12, 192.168/16 and `.local` names are accepted. Only the Pi address is remembered; the access token stays in dashboard memory for that session.

The embedded dashboard provides status, video preview, manual pan/tilt, track mode, STOP/HOLD and calibration. On app backgrounding, it requests STOP; if the app or connection fails, the Pi's 1-second browser lease and ESP32 watchdog stop further movement. A STOP holds the last PWM and is not a power disconnect. Returning to the app never automatically enables the mount.

The Pi HTTP interface is unencrypted. Keep it on a trusted isolated LAN; avoid public Wi-Fi and router port forwarding. Android cleartext permission is needed for this local HTTP connection. Test servo directions with horns detached, then validate the system on real hardware according to `docs/SPEC.md`.

## Update button and signing

**Check for update** retrieves a verified public GitHub release and opens Android's installer. It has no stored GitHub credential. The first public signed release needs a stable signing key in repository Actions secrets; see [`docs/UPDATES.md`](../docs/UPDATES.md). Existing debug builds cannot upgrade in place to the first signed release because the certificates differ.
