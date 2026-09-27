# Verification record — 2026-09-27

## 0.2.0 control-layout candidate

Two-axis touch control with spring-return joysticks and camera center pane added. The Pi API now has manual HOLD, setting the target to the current commanded PWM when a stick is released. GitHub Actions Android run 36313056442 succeeded and produced the debug APK; downloaded APK ZIP CRC passed, size 10,509 bytes and SHA-256 `171316d2dd1f6154ceb641a1ecabf362141e1f4f3a670d21966bc2b09bbd7f2c`. CI run 36313058496 succeeded, including API, browser, firmware and packaging checks. Hardware direction and response must be measured against actual servo horn geometry; numeric pulse direction alone does not establish camera-left/right/up/down. Pi deployment and physical phone/servo testing remain open.

## Follow-up review (software only)

Android operator app added with local Pi address entry, dashboard access, background STOP request and debug APK CI workflow. GitHub Actions run 36312512126 built and uploaded `app-debug.apk` from commit 3355bc0; the downloaded APK is 10,509 bytes, ZIP CRC passed, and SHA-256 is `288e38b1114ecf3e427111eef09cc0a9984720b421492df326ee1ceb5ea91b60`. Installation and all phone/Pi connection flows remain unverified until physical testing.

The vision worker now drops frames older than 0.75 s both before and after inference, preventing expensive JPEG encoding and delivery of already stale results. It also releases the camera on worker exit. Physical capture age remains an estimate based on when OpenCV returns the frame, not exposure time. The new frame-age regression test was added. This workspace lacks pytest and dependency installation could not reach the package index, so the full suite must be rerun in CI or the provisioned development environment before packaging. No hardware acceptance status changes.

Environment: Linux x86_64, Python3.12.14. No physical Pi, ESP32, webcam or servos attached. This is a bench-testing candidate, not a hardware-qualified release.

| Check | Actual result |
|---|---|
| `python -m pytest -q` | 28 passed (4.41s in recorded final run) |
| Native C++ firmware guard | Compiled with g++ C++11, `-Wall -Wextra -Werror`; assertions passed |
| Protocol interoperability | Firmware-generated ACK decoded by Python; known CRC vector,128 single-bit corruptions, noise/fragmentation tested |
| Serial integration | Real Linux pseudoterminal/pyserial handshake and ACK timeout passed; no USB hardware involved |
| HTTP/operator flows | Authentication, input rejection, manual control, config persistence, target/link loss,1s lease and no auto-rearm passed |
| Missing-model process | Spawned worker returns actionable error without touching hardware |
| Python package | Wheel and sdist built; wheel installed in separate venv; version0.1.0 launches; dashboard asset bytes match source |
| Version consistency | VERSION, project metadata, Python, firmware, dashboard and package.json match0.1.0 |
| JavaScript | `node --check` passed |
| Python hygiene | Ruff unused/undefined-name checks passed; source formatted |
| Python dependency audit | pip-audit2.9.0:58 evaluated runtime/vision/NCNN packages, zero known advisories after fixes; five directly pinned build tools also zero known advisories |
| Node development audit | npm audit:zero reported vulnerabilities |
| ARM dependency availability | Lock contains CPython3.11/aarch64 wheels for torch2.13.0, torchvision0.28.0, NumPy, OpenCV and NCNN; not an actual Pi installation test |
| Browser render / click test | BLOCKED: browser executable unavailable; browser downloads returned truncated/invalid archives. Test script supplied and CI gate configured; not executed successfully here |
| Full ESP32 firmware build | Pending final build result; see final status below |
| GitHub Actions/Release | Not run/published. Public destination approval pending |

## Security review and fixes

Removed unused Python imports, pinned/resolved dependencies, bounded requests and serial parsing, token-authenticated all API routes, rejected cross-origin control, defaulted to localhost, set CSP/no-store/nosniff, limited HTTP worker concurrency, and prohibited calibration changes while enabled. No secrets/keys/weights/recordings are included. Application still requires a trusted host/USB and trusted model weights; HTTP LAN mode is not encrypted. No security certification is claimed. Audits reflect the database responses for evaluated packages, not proof of absence of vulnerabilities or full embedded-framework audit.

Initial audit flagged torch2.10.0 (PYSEC-2026-139, GHSA-rrmf-rvhw-rf47); replaced with2.13.0 and matching torchvision0.28.0, re-resolved and re-audited. Build audit flagged setuptools82.0.1 (PYSEC-2026-3447); replaced with84.0.0. No findings were suppressed.

## Not tested

Actual YOLO model inference/export; Pi installation, FPS, RAM, thermal throttling and capture latency; webcam UVC compatibility; physical PWM/servo directions, mechanical limits, holding behavior and electrical watchdog timing; BEC current/power integrity; real subject association; moving-rover operation; systemd installation; firmware flashing; signed/secure boot; GitHub workflow execution. All relevant physical acceptance gates are in SPEC.md.
