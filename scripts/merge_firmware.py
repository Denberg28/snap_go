"""Merge the standard PlatformIO ESP32-S3 bootloader/partition/application images."""

from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
v = (root / "VERSION").read_text().strip()
build = root / "firmware/.pio/build/esp32-s3-devkitc-1"
framework = Path.home() / ".platformio/packages/framework-arduinoespressif32"
subprocess.run(
    [
        sys.executable,
        "-m",
        "esptool",
        "--chip",
        "esp32s3",
        "merge_bin",
        "-o",
        str(root / "firmware" / f"Snap_Go-{v}-esp32s3.bin"),
        "--flash_mode",
        "dio",
        "--flash_size",
        "8MB",
        "0x0000",
        str(build / "bootloader.bin"),
        "0x8000",
        str(build / "partitions.bin"),
        "0xe000",
        str(framework / "tools/partitions/boot_app0.bin"),
        "0x10000",
        str(build / "firmware.bin"),
    ],
    check=True,
)
