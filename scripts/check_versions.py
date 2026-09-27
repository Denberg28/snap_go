from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
v = (root / "VERSION").read_text().strip()
for name, pattern in [
    ("pyproject.toml", r'version = "([^"]+)"'),
    ("snap_go/__init__.py", r'__version__ = "([^"]+)"'),
    ("firmware/src/main.cpp", r"Snap_Go ([0-9.]+)\."),
    ("snap_go/static/index.html", r'id="version">([^<]+)'),
]:
    match = re.search(pattern, (root / name).read_text())
    assert match and match.group(1) == v, (name, match.group(1) if match else None, v)
import json

assert json.loads((root / "package.json").read_text())["version"] == v
print("Version consistent:", v)
