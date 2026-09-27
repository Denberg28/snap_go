from dataclasses import asdict
import json
import pytest
from snap_go.control import Config, Controller, save_config


def ready(mode="manual", now=10):
    c = Controller()
    c.link_ok = True
    c.frame_time = now
    c.enable(mode, now)
    return c


def detection(x=0.7, y=0.5):
    return dict(x=x, y=y, class_id=0, confidence=0.9)


def test_startup_and_reenable_guards():
    c = Controller()
    assert not c.enabled
    with pytest.raises(ValueError):
        c.enable("manual", 10)
    c.link_ok = True
    with pytest.raises(ValueError):
        c.enable("track", 10)
    with pytest.raises(ValueError):
        c.enable("bad", 10)


@pytest.mark.parametrize(
    "fault,reason",
    [("lease", "lease"), ("link", "Serial"), ("camera", "stale"), ("target", "Target")],
)
def test_faults_latch_disabled(fault, reason):
    c = ready("track")
    c.lease = 12
    c.frame_time = 12
    c.seen = 12
    if fault == "lease":
        c.lease = 10
    if fault == "link":
        c.link_ok = False
    if fault == "camera":
        c.frame_time = 10
    if fault == "target":
        c.seen = 10
    c.tick(12, 0.05)
    assert not c.enabled and reason in c.reason
    c.link_ok = True
    c.frame_time = 13
    c.seen = 13
    c.lease = 13
    c.tick(13, 0.05)
    assert not c.enabled


def test_speed_and_limits():
    c = ready()
    c.target = [1800, 1700]
    c.tick(10.05, 0.05)
    assert c.pan == 1509 and c.tilt == 1509
    for _ in range(1000):
        c.tick(10, 0.05)
    assert c.pan == 1800 and c.tilt == 1700


def test_target_selection_hysteresis_and_no_blind_motion():
    c = ready("track")
    c.observe([detection()], 10.01, 10.01)
    c.tick(10.02, 0.05)
    assert c.pan > 1500
    old = c.pan
    c.observe([detection(0.05)], 10.03, 10.03)
    c.tick(10.04, 0.05)
    assert c.pan == old
    c.observe([detection(0.75)], 9, 10.05)
    assert c.frame_time == 10.03


def test_deadband_reverse_and_ack_position():
    c = ready("track")
    c.observe([detection(0.52, 0.6)], 10.01, 10.01)
    c.tick(10.02, 0.05)
    assert c.pan == 1500 and c.tilt < 1500
    c.stop()
    c.actual = [1550, 1520]
    c.enable("manual", 10.1)
    assert c.pan == 1550 and c.target == [1550, 1520]


@pytest.mark.parametrize(
    "field,value",
    [
        ("speed", float("nan")),
        ("gain", float("inf")),
        ("pan_min", 1000),
        ("pan_max", 1500),
        ("pan_reverse", 1),
        ("class_id", 80),
        ("class_id", True),
        ("confidence", 1),
        ("speed", True),
    ],
)
def test_bad_config(field, value):
    data = asdict(Config())
    data[field] = value
    with pytest.raises(ValueError):
        Config.validate(data)


def test_atomic_settings(tmp_path):
    p = tmp_path / "config.json"
    save_config(p, Config())
    assert Config.validate(json.loads(p.read_text())) == Config()
    assert p.stat().st_mode & 0o777 == 0o600
    assert not p.with_suffix(".tmp").exists()
