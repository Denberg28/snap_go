import random
import pytest
from snap_go.protocol import Parser, CMD, ACK, SIZE, encode, decode


def test_crc_known_vector():
    import binascii

    assert binascii.crc_hqx(b"123456789", 0xFFFF) == 0x29B1


def test_roundtrip_and_every_single_bit_corruption():
    packet = encode(CMD, 0xFFFFFFFF, 1100, 1900, 1)
    assert decode(packet)["seq"] == 0xFFFFFFFF
    for bit in range(128):
        bad = bytearray(packet)
        bad[bit // 8] ^= 1 << (bit % 8)
        with pytest.raises(ValueError):
            decode(bad)


def test_fragmented_noisy_parser():
    parser = Parser()
    packet = encode(ACK, 123)
    stream = b"noiseSGbroken" + packet + b"junk" + packet
    result = []
    for byte in stream:
        result.extend(parser.feed(bytes([byte])))
    assert [p["seq"] for p in result] == [123, 123]
    assert len(parser.buffer) < SIZE


def test_random_noise_bounded():
    p = Parser()
    p.feed(random.Random(32).randbytes(100000))
    assert len(p.buffer) < SIZE
