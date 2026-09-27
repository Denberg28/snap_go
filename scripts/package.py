"""Package tracked source and successful builds; never traverse secrets/untracked files."""

import hashlib
from pathlib import Path
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
v = (root / "VERSION").read_text().strip()
out = root / "dist"
out.mkdir(exist_ok=True)
files = [
    root / p
    for p in subprocess.check_output(
        ["git", "ls-files"], cwd=root, text=True
    ).splitlines()
]
files += (
    list(out.glob("*.whl")) + list(out.glob("*.tar.gz")) + list(out.glob("*.bundle"))
)
merged = root / "firmware" / f"Snap_Go-{v}-esp32s3.bin"
if merged.exists():
    files.append(merged)
archive = out / f"Snap_Go-{v}-testing.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    sums = []
    for path in sorted(set(files)):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        z.writestr(f"Snap_Go-{v}/{rel}", data)
        sums.append(hashlib.sha256(data).hexdigest() + "  " + rel)
    z.writestr(f"Snap_Go-{v}/SHA256SUMS", "\n".join(sums) + "\n")
(out / "SHA256SUMS").write_text(
    "".join(
        hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n"
        for p in sorted(out.iterdir())
        if p.is_file() and p.name != "SHA256SUMS"
    )
)
print(archive)
