"""Hardware-independent control, input validation and persistence."""

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import threading
import time


@dataclass
class Config:
    pan_min: int = 1200
    pan_max: int = 1800
    tilt_min: int = 1300
    tilt_max: int = 1700
    pan_center: int = 1500
    tilt_center: int = 1500
    pan_reverse: bool = False
    tilt_reverse: bool = True
    gain: float = 220.0  # microseconds/second for normalized unit image error
    speed: float = 180.0  # microseconds/second; firmware independently caps 200
    deadband: float = 0.06
    class_id: int = 0  # COCO person
    confidence: float = 0.5

    @classmethod
    def validate(cls, data):
        if not isinstance(data, dict) or set(data) != set(asdict(cls())):
            raise ValueError(
                "Send every calibration field; unknown fields are rejected"
            )
        c = cls(**data)
        for axis in ("pan", "tilt"):
            lo, hi, center = (
                getattr(c, axis + "_" + x) for x in ("min", "max", "center")
            )
            if (
                any(type(x) is not int for x in (lo, hi, center))
                or not 1100 <= lo < center < hi <= 1900
            ):
                raise ValueError(
                    "Limits must be integers: 1100 <= minimum < center < maximum <= 1900"
                )
            if type(getattr(c, axis + "_reverse")) is not bool:
                raise ValueError("Reverse must be boolean")
        for name, lo, hi in [
            ("gain", 10, 400),
            ("speed", 10, 200),
            ("deadband", 0.01, 0.3),
            ("confidence", 0.1, 0.95),
        ]:
            v = getattr(c, name)
            if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
                raise ValueError(f"Invalid {name}: expected {lo} to {hi}")
        if type(c.class_id) is not int or not 0 <= c.class_id <= 79:
            raise ValueError("class_id must be 0 to 79")
        return c


def save_config(path, config):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with open(temp, "w", encoding="utf-8") as f:
        os.chmod(temp, 0o600)
        json.dump(asdict(config), f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


class Controller:
    def __init__(self, config=None):
        self.lock = threading.RLock()
        self.config = config or Config()
        self.enabled = False
        self.mode = "manual"
        self.reason = "Disabled at startup"
        self.pan = float(self.config.pan_center)
        self.tilt = float(self.config.tilt_center)
        self.target = [self.pan, self.tilt]
        self.lease = -1e9
        self.frame_time = -1e9
        self.seen = -1e9
        self.detection = None
        self.selection = None
        self.candidates = []
        self.error = [0.0, 0.0]
        self.fps = 0.0
        self.link_ok = False
        self.actual = None
        self.functions = [False, False, False]

    def stop(self, reason="Disabled by operator"):
        self.enabled = False
        self.functions = [False, False, False]
        self.reason = reason
        self.selection = None
        self.detection = None
        self.error = [0.0, 0.0]
        self.target = [self.pan, self.tilt]

    def enable(self, mode, now):
        if mode not in ("manual", "track"):
            raise ValueError("Mode must be manual or track")
        if not self.link_ok:
            raise ValueError("ESP32 link is not ready")
        if mode == "track" and now - self.frame_time > 0.75:
            raise ValueError("No fresh camera detections; check camera and model")
        # Always begin at the acknowledged held position, avoiding a resume jump.
        if self.actual:
            self.pan, self.tilt = map(float, self.actual)
        self.target = [self.pan, self.tilt]
        self.enabled, self.mode, self.lease = True, mode, now
        self.seen = now
        if self.selection is None:
            self.detection = None
        self.error = [0.0, 0.0]
        self.reason = "Enabled: " + mode

    def observe(self, detections, timestamp, now):
        if now - timestamp > 0.75 or timestamp > now or timestamp <= self.frame_time:
            return
        self.frame_time = timestamp
        candidates = [
            d
            for d in detections
            if d["class_id"] == self.config.class_id
            and d["confidence"] >= self.config.confidence
        ]
        # Expose at most three strong candidates; never silently switch a selected target.
        candidates.sort(key=lambda d: d["confidence"], reverse=True)
        if self.selection is not None:
            anchor = self.detection
            candidates = [d for d in candidates if anchor and math.hypot(d["x"]-anchor["x"], d["y"]-anchor["y"]) <= 0.25]
        elif self.detection:
            candidates = [d for d in candidates if math.hypot(d["x"]-self.detection["x"], d["y"]-self.detection["y"]) <= 0.25]
        self.candidates = sorted([d for d in detections if d["class_id"] == self.config.class_id and d["confidence"] >= self.config.confidence], key=lambda d: d["confidence"], reverse=True)[:3]
        if candidates:
            anchor = self.detection or {"x": 0.5, "y": 0.5}
            self.detection = min(
                candidates,
                key=lambda d: (d["x"] - anchor["x"]) ** 2 + (d["y"] - anchor["y"]) ** 2,
            )
            self.seen = timestamp
            self.error = [2 * (self.detection[k] - 0.5) for k in ("x", "y")]
        else:
            self.detection = None
            self.error = [0.0, 0.0]  # hold immediately; no blind scanning

    @staticmethod
    def _inside_selection(d, rect):
        x1, y1, x2, y2 = rect
        return x1 <= d["x"] <= x2 and y1 <= d["y"] <= y2

    def select(self, rect, now):
        if not isinstance(rect, list) or len(rect) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in rect):
            raise ValueError("Selection must be four normalized coordinates")
        x1, y1, x2, y2 = rect
        if x2-x1 < .02 or y2-y1 < .02:
            raise ValueError("Draw a larger selection rectangle")
        if now-self.frame_time > .75:
            raise ValueError("Camera frame is stale")
        matches = [d for d in self.candidates if self._inside_selection(d, rect)]
        if not matches:
            raise ValueError("No detected target inside the rectangle")
        self.selection = rect
        self.detection = max(matches, key=lambda d:d["confidence"])
        self.seen = now
        self.reason = "Target selected"

    def tick(self, now, dt):
        if not self.enabled and not any(self.functions):
            return
        if not self.link_ok:
            self.stop("Serial link lost; re-enable required")
        elif now - self.lease > 1.0:
            self.stop("Browser control lease expired; re-enable required")
        elif self.mode == "track" and now - self.frame_time > 0.75:
            self.stop("Camera/inference stale; re-enable required")
        elif self.mode == "track" and now - self.seen > 1.0:
            self.stop("Target lost; re-enable to select a new target")
        if not self.enabled:
            return
        dt = min(max(dt, 0), 0.1)
        for i, axis in enumerate(("pan", "tilt")):
            current = getattr(self, axis)
            if self.mode == "track":
                err = self.error[i]
                delta = (
                    0
                    if abs(err) <= self.config.deadband
                    else err * self.config.gain * dt
                )
                if getattr(self.config, axis + "_reverse"):
                    delta = -delta
            else:
                delta = self.target[i] - current
            step = self.config.speed * dt
            value = current + max(-step, min(step, delta))
            setattr(
                self,
                axis,
                max(
                    getattr(self.config, axis + "_min"),
                    min(getattr(self.config, axis + "_max"), value),
                ),
            )

    def status(self, now=None):
        now = time.monotonic() if now is None else now
        return dict(
            enabled=self.enabled,
            mode=self.mode,
            reason=self.reason,
            pan=round(self.pan),
            tilt=round(self.tilt),
            actual=self.actual,
            link_ok=self.link_ok,
            camera_ok=now - self.frame_time <= 0.75,
            fps=round(self.fps, 1),
            target=self.detection,
            candidates=list(self.candidates),
            selection=self.selection,
            functions=list(self.functions),
            config=asdict(self.config),
        )
