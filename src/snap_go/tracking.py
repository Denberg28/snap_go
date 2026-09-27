from __future__ import annotations
from dataclasses import dataclass
from time import monotonic
from .config import Calibration

@dataclass
class TrackConfig:
    deadband_x: float = 0.08
    deadband_y: float = 0.08
    gain_pan: float = 18.0
    gain_tilt: float = 14.0
    max_step_deg: float = 4.0
    stale_after_s: float = 0.35

@dataclass
class Detection:
    cx: float
    cy: float
    confidence: float
    seen_at: float

class Tracker:
    def __init__(self, cal: Calibration, cfg: TrackConfig | None = None):
        self.cal, self.cfg = cal, cfg or TrackConfig()
        self.pan, self.tilt = cal.pan_center, cal.tilt_center
        self.enabled = False

    def center(self) -> tuple[float, float]:
        self.pan, self.tilt = self.cal.pan_center, self.cal.tilt_center
        return self.pan, self.tilt

    def manual(self, pan: float, tilt: float) -> tuple[float, float]:
        self.pan, self.tilt = self.cal.clamp(pan, tilt)
        return self.pan, self.tilt

    def update(self, det: Detection | None, now: float | None = None) -> tuple[float, float, str]:
        now = monotonic() if now is None else now
        if not self.enabled: return self.pan, self.tilt, "disabled"
        if det is None or now - det.seen_at > self.cfg.stale_after_s: return self.pan, self.tilt, "stale"
        ex, ey = det.cx - 0.5, det.cy - 0.5
        dp = 0.0 if abs(ex) <= self.cfg.deadband_x else ex * self.cfg.gain_pan
        dt = 0.0 if abs(ey) <= self.cfg.deadband_y else ey * self.cfg.gain_tilt
        dp = max(-self.cfg.max_step_deg, min(self.cfg.max_step_deg, dp))
        dt = max(-self.cfg.max_step_deg, min(self.cfg.max_step_deg, dt))
        if self.cal.pan_invert: dp = -dp
        if self.cal.tilt_invert: dt = -dt
        self.pan, self.tilt = self.cal.clamp(self.pan + dp, self.tilt + dt)
        return self.pan, self.tilt, "tracking"
