from argparse import Namespace
from dataclasses import asdict
import json
import threading
import time
import urllib.request
import urllib.error
import pytest
from snap_go.app import Runtime, Server, handler


@pytest.fixture
def app(tmp_path):
    r = Runtime(Namespace(simulate=True, config=str(tmp_path / "settings.json")))
    r.start()
    server = Server(("127.0.0.1", 0), handler(r, "x" * 32))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield r, "http://127.0.0.1:" + str(server.server_port)
    server.shutdown()
    server.server_close()
    r.close()


def call(url, payload=None, token="x" * 32, origin=None):
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    if origin:
        headers["Origin"] = origin
    req = urllib.request.Request(
        url,
        headers=headers,
        data=json.dumps(payload).encode() if payload is not None else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_operator_flow_persistence_and_lease(app):
    r, url = app
    assert call(url + "/api/status", token="bad")[0] == 401
    status, data = call(url + "/api/status")
    assert status == 200 and data["simulate"] and not data["enabled"]
    assert call(url + "/api/control", {"action": "enable", "mode": "manual"})[1][
        "enabled"
    ]
    assert (
        call(url + "/api/control", {"action": "move", "pan": 1600, "tilt": 1500})[0]
        == 200
    )
    f1 = call(url + "/api/control", {"action": "function", "index": 1, "enabled": True})[1]
    assert f1["functions"] == [True, False, False]
    assert call(url + "/api/control", {"action": "hold"})[0] == 200
    assert r.control.target == [r.control.pan, r.control.tilt]
    assert (
        call(url + "/api/control", {"action": "move", "pan": 9999, "tilt": 1500})[0]
        == 400
    )
    assert (
        call(
            url + "/api/control",
            {"action": "config", "config": asdict(r.control.config)},
        )[0]
        == 400
    )
    # Closing/losing browser stops motion and function outputs without relying on a stop request.
    time.sleep(1.2)
    expired = call(url + "/api/status")[1]
    assert not expired["enabled"] and expired["functions"] == [False, False, False]
    cfg = asdict(r.control.config)
    cfg["pan_reverse"] = True
    assert call(url + "/api/control", {"action": "config", "config": cfg})[0] == 200
    assert json.loads(r.path.read_text())["pan_reverse"]
    r2 = Runtime(r.args)
    assert r2.control.config.pan_reverse and not r2.control.enabled


def test_cross_origin_and_malformed(app):
    _, url = app
    assert (
        call(
            url + "/api/control", {"action": "stop"}, origin="http://attacker.example"
        )[0]
        == 403
    )
    assert call(url + "/api/control", [])[0] == 400
    assert call(url + "/api/control", {"action": "bogus"})[0] == 400


def test_tracking_target_loss_and_link_restore_do_not_rearm(app):
    r, url = app
    assert call(url + "/api/control", {"action": "enable", "mode": "track"})[1][
        "enabled"
    ]
    call(url + "/api/control", {"action": "simulate", "fault": "target"})
    for _ in range(6):
        call(url + "/api/control", {"action": "lease"})
        time.sleep(0.2)
    assert not call(url + "/api/status")[1]["enabled"]
    call(url + "/api/control", {"action": "simulate", "fault": "none"})
    assert not call(url + "/api/status")[1]["enabled"]
    call(url + "/api/control", {"action": "enable", "mode": "manual"})
    call(url + "/api/control", {"action": "simulate", "fault": "serial"})
    time.sleep(0.1)
    assert not call(url + "/api/status")[1]["enabled"]
