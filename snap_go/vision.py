"""Isolated worker: a blocked camera/model cannot block servo failsafes."""

import os
import queue
import time
from pathlib import Path


MAX_FRAME_AGE = 0.75


def frame_is_fresh(stamp, now):
    """Reject buffered frames and results that missed the control deadline."""
    return 0 <= now - stamp <= MAX_FRAME_AGE


def latest_put(channel, value):
    try:
        channel.put_nowait(value)
    except queue.Full:
        try:
            channel.get_nowait()
        except queue.Empty:
            pass
        try:
            channel.put_nowait(value)
        except queue.Full:
            pass


def worker(channel, shutdown, camera, model_path):
    cap = None
    try:
        # Never silently download weights during startup.
        if not Path(model_path).exists():
            raise RuntimeError(
                "Model missing; provision yolov8n.pt before hardware mode"
            )
        os.environ.setdefault("YOLO_AUTOINSTALL", "false")
        import cv2
        import torch
        from ultralytics import YOLO

        torch.set_num_threads(2)
        cv2.setNumThreads(1)
        model = YOLO(model_path, task="detect")
        cap = cv2.VideoCapture(camera, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            raise RuntimeError(
                "Webcam unavailable; check /dev/video devices and video group"
            )
        # Separate capture thread keeps only the newest frame while inference runs.
        import threading

        frames = queue.Queue(maxsize=1)

        def capture():
            while not shutdown.is_set():
                ok, frame = cap.read()
                if not ok:
                    latest_put(frames, (time.monotonic(), None))
                    return
                latest_put(frames, (time.monotonic(), frame))

        threading.Thread(target=capture, daemon=True).start()
        while not shutdown.is_set():
            stamp, frame = frames.get(timeout=2)
            if frame is None:
                raise RuntimeError("Webcam disconnected or frame read failed")
            start = time.monotonic()
            if not frame_is_fresh(stamp, start):
                continue
            result = model.predict(
                frame, imgsz=320, conf=0.1, device="cpu", verbose=False
            )[0]
            if not frame_is_fresh(stamp, time.monotonic()):
                continue
            height, width = frame.shape[:2]
            detections = []
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    dict(
                        x=(x1 + x2) / (2 * width),
                        y=(y1 + y2) / (2 * height),
                        box=[x1 / width, y1 / height, x2 / width, y2 / height],
                        confidence=float(box.conf[0]),
                        class_id=int(box.cls[0]),
                    )
                )
            ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
            latest_put(
                channel,
                dict(
                    timestamp=stamp,
                    detections=detections,
                    fps=1 / max(time.monotonic() - start, 0.001),
                    jpeg=jpg.tobytes() if ok else b"",
                    error="",
                ),
            )
    except Exception as exc:
        latest_put(channel, dict(error=f"{type(exc).__name__}: {exc}"))
    finally:
        if cap is not None:
            cap.release()
