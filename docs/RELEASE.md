# Release, installation, upgrade and rollback

Version0.1.0, bench-testing candidate. Read VERIFICATION.md before flashing. Package contains source, Python wheel/sdist, checksums and firmware only if the build succeeded. Do not imply a firmware binary exists when absent.

## Deploy Python package

Extract the archive. Install `dist/snap_go-0.1.0-py3-none-any.whl` into a dedicated Python3.10–3.12 virtual environment, or install source with `pip install '.[vision]'`. The wheel includes the dashboard but not weights, PyTorch/OpenCV, firmware or system packages. First install and model provisioning need Internet; operational inference/control are local. Full offline installation requires separately caching architecture-matching dependency wheels and weights; those large dependencies are not bundled.

## Flash a supplied ESP32 binary

Prefer the PlatformIO upload command in README, which uses correct offsets. If the archive contains a merged `firmware/Snap_Go-0.1.0-esp32s3.bin`, use:

```bash
python -m pip install esptool==4.8.1
python -m esptool --chip esp32s3 --port YOUR_SERIAL_PORT --baud 460800 write_flash 0x0 firmware/Snap_Go-0.1.0-esp32s3.bin
```

Confirm reference board and disconnect servo power before flashing. There is no firmware signing identity or secure boot in this candidate. Do not enable eFuses or flash secure-boot settings as part of testing. No OTA updater is included.

## Optional systemd

Create a dedicated `snapgo` user with dialout and video groups. Install under `/opt/snap-go`, configure a long random token in `/etc/snap-go.env` (root-owned0600) and use `deploy/snap-go.service` as a template. That service assumes a venv at `/opt/snap-go/.venv` and model under `/opt/snap-go/models`. Set a stable serial-by-id path. Copy the unit to `/etc/systemd/system`, run `systemctl daemon-reload`, then `systemctl enable --now snap-go`. Never run the application as root. CLI configuration file lives under your home by default; the unit explicitly uses `/var/lib/snap-go/config.json`.

## Upgrade

Stop the service and remove servo power. Back up calibration JSON and `/etc/snap-go.env` privately (never git). Keep the last working source archive/wheel/firmware and environment lock. Build a separate versioned virtual environment, install and test in simulation first. Flash matching firmware when protocol changes require it. Switch service path, restart disabled, verify diagnostics/manual center/STOP, then tracking. This version has no config migration; future versions must reject unsupported settings rather than guess.

## Rollback

Stop service, remove servo power, restore prior venv/service path and backed-up calibration. Flash prior known-working firmware if changed. Restart disabled and repeat manual/STOP checks. v0.1.0 is the first release: if no prior Snap_Go exists, rollback means stopping/disabling the service and disconnecting the independent camera module. ArduRover settings are never changed.

## Publish after owner authorization

The existing destination is public. Do not publish until the user explicitly approves public source/release or makes the repository private. Local tag `v0.1.0` marks this candidate; no remote tag/release exists until publication is performed.

From the repository root, after checking credentials outside the repository:

```bash
git remote add origin https://github.com/denberg28/snap_go.git
git push -u origin main
git push origin v0.1.0
```

The tag workflow runs tests/build and creates a **prerelease** with source, wheel, firmware and SHA-256 checksums. It uses only the ephemeral GitHub Actions token (`contents:write` in the release job). No PAT/signing key is required. Inspect its result before telling anyone the release is available. Do not claim it ran based only on the workflow file.

The testing ZIP also carries a Git bundle with the local main branch and v0.1.0 tag. To recover history, run `git clone dist/Snap_Go-0.1.0.bundle snap_go`; its default origin is the local bundle, so use `git remote set-url origin https://github.com/denberg28/snap_go.git` only after publication authorization. No remote credentials are stored in the bundle.
