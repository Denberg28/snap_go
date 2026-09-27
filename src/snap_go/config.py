from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass
class Calibration:
    pan_min: float = 30.0
    pan_max: float = 150.0
    tilt_min: float = 45.0
    tilt_max: float = 135.0
    pan_center: float = 90.0
    tilt_center: float = 90.0
    pan_invert: bool = False
    tilt_invert: bool = False

    def validate(self) -> None:
        if not (0 <= self.pan_min < self.pan_max <= 180): raise ValueError("invalid pan limits")
        if not (0 <= self.tilt_min < self.tilt_max <= 180): raise ValueError("invalid tilt limits")
        if not (self.pan_min <= self.pan_center <= self.pan_max): raise ValueError("invalid pan center")
        if not (self.tilt_min <= self.tilt_center <= self.tilt_max): raise ValueError("invalid tilt center")

    def clamp(self, pan: float, tilt: float) -> tuple[float, float]:
        return (max(self.pan_min, min(self.pan_max, pan)), max(self.tilt_min, min(self.tilt_max, tilt)))

class CalibrationStore:
    def __init__(self, path: str | Path): self.path = Path(path)
    def load(self) -> Calibration:
        if not self.path.exists(): return Calibration()
        c = Calibration(**json.loads(self.path.read_text()))
        c.validate()
        return c
    def save(self, calibration: Calibration) -> None:
        calibration.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(calibration), indent=2, sort_keys=True))
        tmp.replace(self.path)
