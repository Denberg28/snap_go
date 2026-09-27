from __future__ import annotations
from dataclasses import dataclass
from time import monotonic
from typing import Protocol
from .protocol import encode_message, decode_message

class SerialLike(Protocol):
    def write(self, data: bytes) -> int: ...
    def readline(self) -> bytes: ...

@dataclass
class LinkStatus:
    connected: bool = False
    last_ack: float | None = None
    last_error: str | None = None

class ServoLink:
    def __init__(self, serial_obj: SerialLike):
        self.serial = serial_obj
        self.seq = 0
        self.status = LinkStatus(connected=True)

    def command(self, pan: float, tilt: float, output_enabled: bool = True) -> dict:
        self.seq += 1
        payload = {"type":"servo","seq":self.seq,"pan":round(float(pan),2),"tilt":round(float(tilt),2),"output":bool(output_enabled)}
        self.serial.write(encode_message(payload))
        try:
            ack = decode_message(self.serial.readline())
            if ack.get("type") != "ack" or ack.get("seq") != self.seq:
                raise ValueError("bad ack")
            self.status.last_ack = monotonic()
            self.status.last_error = None
            return ack
        except Exception as exc:
            self.status.last_error = str(exc)
            raise
