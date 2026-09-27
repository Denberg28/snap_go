import os
import pty
import time
from snap_go.transport import SerialLink
from snap_go.protocol import Parser, ACK, encode


def test_real_serial_pty_handshake_and_ack_timeout():
    master, slave = pty.openpty()
    os.set_blocking(master, False)
    link = SerialLink(os.ttyname(slave))
    p = Parser()

    def reply():
        time.sleep(0.005)
        for f in p.feed(os.read(master, 4096)):
            os.write(master, encode(ACK, f["seq"], f["pan"], f["tilt"], f["flags"]))
        time.sleep(0.005)

    try:
        now = time.monotonic()
        assert not link.step(now, 1500, 1500, True)[0]
        reply()
        assert link.step(time.monotonic(), 1500, 1500, False)[0]
        reply()
        assert link.step(time.monotonic(), 1510, 1500, True)[0]
        # Drop all subsequent replies. Old ACK must not establish health.
        assert not link.step(time.monotonic() + 0.5, 1510, 1500, True)[0]
        assert not link.synced
        time.sleep(0.005)
        frames = p.feed(os.read(master, 4096))
        assert frames[-1]["flags"] == 0
    finally:
        link.close()
        os.close(master)
        os.close(slave)
