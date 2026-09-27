"""Read-only host diagnostics; never opens servo control or sends motion."""

import importlib.metadata
import platform
import sys
from pathlib import Path

print("Python:", sys.version.split()[0], "Machine:", platform.machine())
print("Supported Python:", (3, 10) <= sys.version_info[:2] < (3, 13))
for pkg in ("snap-go", "pyserial", "ultralytics", "torch", "opencv-python", "ncnn"):
    try:
        print(pkg, importlib.metadata.version(pkg))
    except importlib.metadata.PackageNotFoundError:
        print(pkg, "not installed")
print(
    "Video devices:", ", ".join(str(p) for p in Path("/dev").glob("video*")) or "none"
)
print(
    "Stable serial devices:",
    ", ".join(str(p) for p in Path("/dev/serial/by-id").glob("*")) or "none",
)
print(
    "This check does not verify wiring, camera capture, inference or physical servo motion."
)
