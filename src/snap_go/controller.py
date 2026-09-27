from __future__ import annotations
from dataclasses import dataclass, asdict
from .tracking import Tracker
from .link import ServoLink

@dataclass
class ControllerStatus:
    tracking: bool = False
    output_enabled: bool = False
    pan: float = 90.0
    tilt: float = 90.0
    last_reason: str = "boot"
    link: str = "not-configured"
    last_error: str | None = None

class SnapGoController:
    def __init__(self, tracker: Tracker, link: ServoLink | None = None):
        self.tracker = tracker
        self.link = link
        self.status = ControllerStatus(pan=tracker.pan, tilt=tracker.tilt, link="connected" if link else "not-configured")

    def snapshot(self) -> dict:
        return asdict(self.status)

    def _send(self, pan: float, tilt: float, output: bool) -> None:
        if self.link is None:
            self.status.link = "not-configured"
            return
        try:
            self.link.command(pan, tilt, output)
            self.status.link = "connected"
            self.status.last_error = None
        except Exception as exc:
            self.status.link = "fault"
            self.status.last_error = str(exc)
            self.tracker.enabled = False
            self.status.tracking = False
            raise

    def set_tracking(self, enabled: bool) -> dict:
        self.tracker.enabled = bool(enabled)
        self.status.tracking = self.tracker.enabled
        self.status.last_reason = "tracking-enabled" if enabled else "tracking-disabled"
        return self.snapshot()

    def manual(self, pan: float, tilt: float) -> dict:
        self.tracker.enabled = False
        self.status.tracking = False
        pan, tilt = self.tracker.manual(pan, tilt)
        self._send(pan, tilt, True)
        self.status.pan, self.status.tilt = pan, tilt
        self.status.output_enabled = True
        self.status.last_reason = "manual"
        return self.snapshot()

    def center(self) -> dict:
        self.tracker.enabled = False
        self.status.tracking = False
        pan, tilt = self.tracker.center()
        self._send(pan, tilt, True)
        self.status.pan, self.status.tilt = pan, tilt
        self.status.output_enabled = True
        self.status.last_reason = "center"
        return self.snapshot()

    def release(self) -> dict:
        self.tracker.enabled = False
        self.status.tracking = False
        self._send(self.tracker.pan, self.tracker.tilt, False)
        self.status.output_enabled = False
        self.status.last_reason = "released"
        return self.snapshot()
