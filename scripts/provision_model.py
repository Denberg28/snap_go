"""Explicit one-time trusted upstream YOLOv8n model download; records hash."""

import hashlib
import os
from pathlib import Path
from ultralytics import YOLO

folder = Path(__file__).resolve().parents[1] / "models"
folder.mkdir(exist_ok=True)
os.chdir(folder)
YOLO("yolov8n.pt")
path = folder / "yolov8n.pt"
digest = hashlib.sha256(path.read_bytes()).hexdigest()
(folder / "SHA256SUMS").write_text(f"{digest}  yolov8n.pt\n")
print("Provisioned", path, "SHA256:", digest)
