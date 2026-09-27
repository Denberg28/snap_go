"""Fixed 16-byte, little-endian protocol; CRC-16/CCITT-FALSE."""

import binascii
import struct

MAGIC = b"SG"
CMD, ACK = 1, 2
ENABLED, FAULT = 1, 2
F1, F2, F3 = 4, 8, 16
FUNCTION_MASK = F1 | F2 | F3
CONTROL_MASK = ENABLED | FUNCTION_MASK
ACK_MASK = CONTROL_MASK | FAULT
BODY = struct.Struct("<2sBBIHHBB")
SIZE = 16


def encode(kind, seq, pan=1500, tilt=1500, flags=0):
    body = BODY.pack(MAGIC, 1, kind, seq & 0xFFFFFFFF, pan, tilt, flags, 0)
    return body + struct.pack("<H", binascii.crc_hqx(body, 0xFFFF))


def decode(frame):
    if len(frame) != SIZE or binascii.crc_hqx(frame[:14], 0xFFFF) != int.from_bytes(
        frame[14:], "little"
    ):
        raise ValueError("CRC or length")
    magic, version, kind, seq, pan, tilt, flags, reserved = BODY.unpack(frame[:14])
    allowed = CONTROL_MASK if kind == CMD else ACK_MASK
    if (
        magic != MAGIC
        or version != 1
        or kind not in (CMD, ACK)
        or reserved
        or flags & ~allowed
        or (kind == CMD and flags & FAULT)
    ):
        raise ValueError("Protocol header")
    if not 1100 <= pan <= 1900 or not 1100 <= tilt <= 1900:
        raise ValueError("Pulse outside hard limits")
    return dict(kind=kind, seq=seq, pan=pan, tilt=tilt, flags=flags)


class Parser:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        result = []
        while len(self.buffer) >= SIZE:
            if self.buffer[:2] != MAGIC:
                del self.buffer[0]
                continue
            try:
                result.append(decode(self.buffer[:SIZE]))
                del self.buffer[:SIZE]
            except ValueError:
                del self.buffer[0]
        return result
