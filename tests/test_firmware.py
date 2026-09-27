from pathlib import Path
import subprocess
from snap_go.protocol import decode, ACK


def test_native_firmware_guard_and_cross_language_ack(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "guard"
    subprocess.run(
        [
            "g++",
            "-std=c++11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I" + str(root / "firmware/include"),
            str(root / "tests/firmware_native.cpp"),
            "-o",
            str(exe),
        ],
        check=True,
    )
    result = subprocess.check_output([str(exe)], text=True).strip()
    frame = decode(bytes.fromhex(result))
    assert frame == dict(kind=ACK, seq=0x12345678, pan=1500, tilt=1600, flags=1)
