"""Single owner serial loop; short ACK deadline and no automatic re-arming."""

from .protocol import Parser, CMD, ACK, ENABLED, FAULT, encode


class SerialLink:
    def __init__(self, port):
        self.port = port
        self.device = None
        self.parser = Parser()
        self.seq = 0
        self.pending = {}
        self.last_ack = -1e9
        self.retry_at = 0.0
        self.synced = False
        self.error = "Waiting for ESP32"
        self.actual = None

    def close(self):
        if self.device:
            self.device.close()
        self.device = None
        self.synced = False
        self.pending.clear()

    def step(self, now, pan, tilt, enabled):
        import serial

        try:
            if self.device is None:
                if now < self.retry_at:
                    return False, None
                self.device = serial.Serial(
                    self.port, 115200, timeout=0, write_timeout=0.05, exclusive=True
                )
                self.device.reset_input_buffer()
                self.parser = Parser()
                self.last_ack = -1e9
                self.synced = False
                self.error = "Waiting for valid firmware acknowledgement"
            for frame in self.parser.feed(
                self.device.read(min(self.device.in_waiting, 4096))
            ):
                sent = self.pending.pop(frame["seq"], None)
                if frame["kind"] != ACK or sent is None or now - sent[0] > 0.3:
                    continue
                if frame["flags"] & FAULT:
                    self.synced = False
                    self.error = "Firmware timeout/fault; re-enable required"
                    continue
                # An ACK must match the enable state requested by that command.
                if bool(frame["flags"] & ENABLED) != sent[1]:
                    self.synced = False
                    self.error = "Firmware state mismatch"
                    continue
                self.last_ack = now
                self.actual = [frame["pan"], frame["tilt"]]
                if not sent[1]:
                    self.synced = True
                self.error = ""
            healthy = self.synced and now - self.last_ack < 0.3
            if not healthy:
                self.synced = False
            self.pending = {k: v for k, v in self.pending.items() if now - v[0] <= 0.3}
            self.seq = (self.seq + 1) & 0xFFFFFFFF
            active = bool(enabled and healthy)
            packet = encode(CMD, self.seq, pan, tilt, ENABLED if active else 0)
            if self.device.write(packet) != len(packet):
                raise serial.SerialTimeoutException("Incomplete serial write")
            self.pending[self.seq] = (now, active)
            if not healthy and not self.error:
                self.error = "ESP32 acknowledgement timeout"
            return healthy, self.actual
        except (OSError, serial.SerialException) as exc:
            self.error = f"Serial unavailable: {exc}"
            self.close()
            self.retry_at = now + 1
            return False, None


class SimLink:
    def __init__(self):
        self.error = ""

    def step(self, now, pan, tilt, enabled):
        return True, [pan, tilt]

    def close(self):
        pass
