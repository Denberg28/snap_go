import multiprocessing as mp
from snap_go.vision import frame_is_fresh, worker


def test_frame_age_gate_discards_delayed_inference_and_future_frames():
    assert frame_is_fresh(10, 10.75)
    assert not frame_is_fresh(10, 10.751)
    assert not frame_is_fresh(11, 10)


def test_missing_model_reports_error_without_hardware(tmp_path):
    ctx = mp.get_context("spawn")
    q = ctx.Queue(maxsize=1)
    stop = ctx.Event()
    p = ctx.Process(target=worker, args=(q, stop, 0, str(tmp_path / "missing.pt")))
    p.start()
    result = q.get(timeout=5)
    p.join(timeout=3)
    assert not p.is_alive() and p.exitcode == 0
    assert "Model missing" in result["error"]
    q.close()
