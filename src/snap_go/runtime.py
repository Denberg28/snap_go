from __future__ import annotations
from dataclasses import dataclass
from time import monotonic, sleep
from typing import Protocol
from .tracking import Tracker, Detection
from .link import ServoLink

class DetectionSource(Protocol):
    def next_detection(self) -> Detection | None: ...

@dataclass
class RuntimeStatus:
    running: bool = False
    frames: int = 0
    commands: int = 0
    last_reason: str = "idle"
    last_error: str | None = None

class TrackingRuntime:
    def __init__(self, tracker: Tracker, source: DetectionSource, link: ServoLink, hz: float = 10.0):
        self.tracker, self.source, self.link = tracker, source, link
        self.period = 1.0 / max(1.0, hz)
        self.status = RuntimeStatus()

    def step(self, now: float | None = None) -> RuntimeStatus:
        now = monotonic() if now is None else now
        try:
            det = self.source.next_detection()
            self.status.frames += 1
            pan, tilt, reason = self.tracker.update(det, now)
            self.status.last_reason = reason
            if self.tracker.enabled and reason == "tracking":
                self.link.command(pan, tilt, output_enabled=True)
                self.status.commands += 1
            self.status.last_error = None
        except Exception as exc:
            self.tracker.enabled = False
            self.status.last_error = str(exc)
            self.status.last_reason = "fault"
        return self.status

    def run(self, should_stop) -> None:
        self.status.running = True
        try:
            while not should_stop():
                started = monotonic()
                self.step(started)
                sleep(max(0.0, self.period - (monotonic() - started)))
        finally:
            self.status.running = False
