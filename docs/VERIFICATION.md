## 0.11.0 testing build
Python control and JS syntax checked. Android and hardware checks pending.

# Verification record — 2026-09-27

## 0.7.0 fixed operator UI candidate

Android Test mode now uses a fixed, overflow-hidden viewport and disables WebView overscroll/scrollbars. The center preview is intentionally non-interactive; only the pan/tilt joysticks accept drag input. The landscape layout narrows the side controls and reduces header/control chrome to increase camera area while keeping the existing offline simulation behavior. Hardware behavior and physical tracking remain unchanged and still require bench validation.


## Signing setup follow-up

The Android release workflow now accepts separate keystore/key passwords, a configurable alias and an expected signing-certificate SHA-256 fingerprint. The APK is checked against that fingerprint before publication. CI runs 36319654168 (project tests) and 36319654144 (debug APK and disposable-key signing path) passed. GitHub has `SNAP_GO_KEY_ALIAS=snapgo`, but its three signing secrets and certificate fingerprint variable are absent as of 2026-09-27 20:42 Asia/Manila. The owner must provide and back up a long-lived signing key before the first stable update. The debug APK retains a disposable signing identity.

The Windows signing setup script creates the keystore locally, refuses to overwrite it and can resume after a partial setup by explicitly reusing the same key. It uses GitHub CLI's stdin secret input so the private values do not appear in command arguments or Git history. PowerShell and GitHub CLI are unavailable in this Linux workspace, so the script's interactive Windows and account setup must be run and verified on the owner's machine. No permanent signing key has been generated or uploaded by this workspace.

## 0.6.0 camera-focused test candidate

The landscape virtual camera now occupies the available height and full center width, with compact side sticks and wrapping controls. Synthetic tracking uses a small center deadband and bounded pan/tilt rates, with on-screen virtual center error. The moving target may lag a little while crossing the scene; a stationary target should settle within the deadband. GitHub Actions CI run 36317462641 passed browser/Pi/firmware checks; Android run 36317462663 passed debug build and disposable-key release-signing verification. APK ZIP CRC passed, includes bundled Test asset, size 26,119 bytes, SHA-256 `a1816f5e6d3809d64132bbf9829d562db6f418fed2ab3bb32fd30d36c99556b2`. Physical tracking performance depends on camera field of view, inference latency, servo speed and calibration; virtual values are not hardware measurements.

## 0.5.0 landscape test candidate

Test mode now requests landscape and restores its mode after Android configuration changes. Android 15+ applies system bar and display cutout insets to the native root to prevent tabs from sitting under status icons. The bundled scene has a compact landscape layout and Moving/Stationary target selector. Stationary freezes world target motion while leaving manual pan/tilt and synthetic tracking usable. Android workflow 36315096711 passed debug and disposable-key signing builds. CI 36315099240 passed browser landscape and motion checks plus Pi/firmware tests. APK ZIP CRC passed; size 25,851 bytes and SHA-256 `869d22d35cc6d064495125b12823404f5369adf2f238f4a50da3657816ad4ee8`. Native rotation, safe padding and real mechanism direction still need device inspection.

## 0.4.0 update candidate

Manual update checker and stable release signing workflow added. The app uses public GitHub release metadata, requires a digest, validates downloaded bytes/package/version/signing certificate and opens Android's installer. No repository token is embedded. Android build 36314438916 passed both debug compilation and a release-signing check with a disposable CI key; debug APK ZIP CRC passed, size 24,775 bytes and SHA-256 `cb44de85ff5fa500caa93b87d3ec910c5cf879191a4b21af0c1886ae615d5526`. CI run 36314442447 passed the Pi/browser/firmware verification. The permanent signing secrets have not been configured and no public signed release exists, so an in-place update cannot yet be exercised. User must install the first stable signed release after removing any ephemeral-key debug build.

## 0.3.0 Live/Test candidate

Android LIVE connects to the Pi dashboard; TEST loads a bundled self-contained HTML simulation with virtual pan/tilt, synthetic person/ball boxes and target following. The local test scene contains no Pi API connection and is labeled offline simulation. Switching from LIVE requests STOP and waits briefly before discarding the live page; the Pi lease and ESP32 watchdog remain independent fallbacks. GitHub Actions Android build 36313604005 passed and produced a signed debug APK, 16,143 bytes, SHA-256 `09f72c169c57d246049f602169d386c4dca2d81df2bd6e36f5aeccec9e68e052`; the APK ZIP CRC passed and includes `assets/test.html`. CI 36313606327 passed, including browser interaction tests for manual virtual pan, target mode, detection toggle, reset, mobile layout and zero network requests from the scene. A test scene is not evidence of real YOLO inference, camera movement, PWM direction or physical safety; these still require on-device checks.

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
