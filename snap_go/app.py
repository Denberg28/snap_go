import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import queue
import secrets
import signal
import threading
import time
from urllib.parse import urlparse
from . import __version__
from .control import Config, Controller, save_config
from .transport import SerialLink, SimLink
from .vision import worker


class Runtime:
    def __init__(self, args):
        self.args = args
        self.path = Path(args.config)
        config = (
            Config.validate(json.loads(self.path.read_text()))
            if self.path.exists()
            else Config()
        )
        self.control = Controller(config)
        self.link = SimLink() if args.simulate else SerialLink(args.serial)
        self.quit = threading.Event()
        self.jpeg = b""
        self.vision_error = ""
        self.process = None
        self.frames = None
        self.thread = None
        self.sim_target = True
        self.sim_link = True

    def start(self):
        if not self.args.simulate:
            ctx = mp.get_context("spawn")
            self.frames = ctx.Queue(maxsize=1)
            self.vision_stop = ctx.Event()
            self.process = ctx.Process(
                target=worker,
                args=(self.frames, self.vision_stop, self.args.camera, self.args.model),
                daemon=True,
            )
            self.process.start()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def loop(self):
        previous = time.monotonic()
        while not self.quit.is_set():
            now = time.monotonic()
            c = self.control
            try:
                with c.lock:
                    if self.args.simulate:
                        detections = (
                            [
                                dict(
                                    x=0.5 + 0.15 * math.sin(now / 3),
                                    y=0.5 + 0.1 * math.cos(now / 4),
                                    confidence=0.95,
                                    class_id=c.config.class_id,
                                    box=[0.5 + 0.15 * math.sin(now / 3)-.04,.3,0.5 + 0.15 * math.sin(now / 3)+.04,.7],
                                ),
                                dict(x=.22,y=.48,confidence=.91,class_id=c.config.class_id,box=[.18,.30,.26,.66]),
                                dict(x=.78+.04*math.sin(now/2),y=.53,confidence=.90,class_id=c.config.class_id,box=[.74+.04*math.sin(now/2),.35,.82+.04*math.sin(now/2),.71]),
                            ]
                            if self.sim_target
                            else []
                        )
                        c.observe(detections, now, now)
                        c.fps = 20
                    else:
                        try:
                            data = self.frames.get_nowait()
                            self.vision_error = data.get("error", "")
                            if not self.vision_error:
                                c.observe(data["detections"], data["timestamp"], now)
                                c.fps = data["fps"]
                                self.jpeg = data["jpeg"]
                        except queue.Empty:
                            pass
                        if (
                            self.process
                            and not self.process.is_alive()
                            and not self.vision_error
                        ):
                            self.vision_error = "Camera worker stopped; restart Snap_Go after resolving camera/model problem"
                    # Tick first: never send an enabled command after a lease/vision expiry.
                    c.tick(now, now - previous)
                    healthy, actual = self.link.step(
                        now, round(c.pan), round(c.tilt), c.enabled, c.functions
                    )
                    c.link_ok = healthy and (
                        self.sim_link if self.args.simulate else True
                    )
                    c.actual = actual
                    if not c.link_ok:
                        c.stop("Serial link lost; re-enable required")
            except Exception as exc:
                with c.lock:
                    c.link_ok = False
                    c.stop(f"Controller fault: {type(exc).__name__}")
                self.vision_error = str(exc)
                self.link.close()
            previous = now
            self.quit.wait(max(0.001, 0.05 - (time.monotonic() - now)))

    def close(self):
        with self.control.lock:
            self.control.stop("Service stopping")
        self.quit.set()
        if self.thread:
            self.thread.join(timeout=1)
        # Best-effort disabled frame; firmware watchdog remains independent.
        try:
            self.link.step(
                time.monotonic(),
                round(self.control.pan),
                round(self.control.tilt),
                False,
                (False, False, False),
            )
        finally:
            self.link.close()
        if self.process:
            self.vision_stop.set()
            self.process.join(timeout=0.5)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=1)
            self.frames.close()

    def action(self, payload):
        c = self.control
        with c.lock:
            op = payload.get("action")
            now = time.monotonic()
            if op == "stop":
                c.stop()
            elif op == "enable":
                c.enable(payload.get("mode"), now)
            elif op == "lease":
                if c.enabled or any(c.functions):
                    c.lease = now
            elif op == "function":
                index = payload.get("index")
                enabled = payload.get("enabled")
                if type(index) is not int or index not in (1, 2, 3) or type(enabled) is not bool:
                    raise ValueError("Function requires index 1-3 and boolean enabled")
                if not c.link_ok:
                    raise ValueError("ESP32 link is not ready")
                c.functions[index - 1] = enabled
                c.lease = now
                c.reason = f"F{index} {'ON' if enabled else 'OFF'}"
            elif op == "select":
                c.select(payload.get("rect"), now)
            elif op == "clear_selection":
                c.selection = None
                c.detection = None
                c.reason = "Target selection cleared"
            elif op == "move":
                if not c.enabled or c.mode != "manual":
                    raise ValueError("Enable manual control first")
                values = [payload.get("pan"), payload.get("tilt")]
                for value, axis in zip(values, ("pan", "tilt")):
                    if (
                        type(value) not in (int, float)
                        or not math.isfinite(value)
                        or not getattr(c.config, axis + "_min")
                        <= value
                        <= getattr(c.config, axis + "_max")
                    ):
                        raise ValueError("Manual target outside calibration limits")
                c.target = values
            elif op == "hold":
                if not c.enabled or c.mode != "manual":
                    raise ValueError("Enable manual control first")
                c.target = [c.pan, c.tilt]
            elif op == "config":
                if c.enabled:
                    raise ValueError("Disable before saving calibration")
                config = Config.validate(payload.get("config"))
                save_config(self.path, config)
                c.config = config
                c.target = [config.pan_center, config.tilt_center]
            elif op == "simulate":
                if not self.args.simulate or payload.get("fault") not in (
                    "none",
                    "target",
                    "serial",
                ):
                    raise ValueError("Simulation fault unavailable")
                self.sim_target = payload["fault"] != "target"
                self.sim_link = payload["fault"] != "serial"
            else:
                raise ValueError("Unknown action")
            return self.status()

    def status(self):
        with self.control.lock:
            return dict(
                self.control.status(),
                version=__version__,
                simulate=self.args.simulate,
                serial_error=self.link.error,
                vision_error=self.vision_error,
            )


def handler(runtime, token):
    static = Path(__file__).parent / "static"

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, fmt, *args):
            pass  # no tokens, camera frames or request bodies in logs

        def send(self, status, data, content_type="application/json"):
            if not isinstance(data, bytes):
                data = json.dumps(data, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            supplied = self.headers.get("Authorization", "")
            return hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode())

        def do_GET(self):
            path = urlparse(self.path).path
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript"),
                "/style.css": ("style.css", "text/css"),
            }
            if path in assets:
                name, mime = assets[path]
                return self.send(200, (static / name).read_bytes(), mime)
            if not self.authorized():
                return self.send(
                    401, {"error": "Enter the access token shown at service startup"}
                )
            if path == "/api/status":
                return self.send(200, runtime.status())
            if path == "/api/frame":
                with runtime.control.lock:
                    jpg = runtime.jpeg
                    fresh = time.monotonic() - runtime.control.frame_time <= 0.75
                return (
                    self.send(200, jpg, "image/jpeg")
                    if jpg and fresh
                    else self.send(503, {"error": "No fresh camera frame"})
                )
            return self.send(404, {"error": "Not found"})

        def do_POST(self):
            if urlparse(self.path).path != "/api/control":
                return self.send(404, {"error": "Not found"})
            if not self.authorized():
                return self.send(401, {"error": "Invalid access token"})
            # No cross-origin mutation, even with an accidentally shared token.
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + self.headers.get("Host", ""):
                return self.send(403, {"error": "Cross-origin control rejected"})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.send(415, {"error": "JSON required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 4096:
                    raise ValueError("Body must be 1–4096 bytes")
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise ValueError("JSON object required")
                result = runtime.action(payload)
                self.send(200, result)
            except (ValueError, TypeError, KeyError) as exc:
                self.send(400, {"error": str(exc)})
            except OSError:
                self.send(
                    500,
                    {
                        "error": "Could not persist settings; previous configuration remains active"
                    },
                )

    return Handler


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # Bound concurrent clients to avoid unbounded thread creation.
    slots = threading.BoundedSemaphore(12)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


def main():
    parser = argparse.ArgumentParser(
        description="Snap_Go: local camera pan/tilt tracking"
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--host", default=os.getenv("SNAP_GO_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("SNAP_GO_PORT", "8080"))
    )
    parser.add_argument("--serial", default=os.getenv("SNAP_GO_SERIAL", "/dev/ttyUSB0"))
    parser.add_argument(
        "--model", default=os.getenv("SNAP_GO_MODEL", "models/yolov8n.pt")
    )
    parser.add_argument(
        "--camera", type=int, default=int(os.getenv("SNAP_GO_CAMERA", "0"))
    )
    parser.add_argument(
        "--config", default=str(Path.home() / ".config/snap-go/config.json")
    )
    args = parser.parse_args()
    token = os.getenv("SNAP_GO_TOKEN") or secrets.token_urlsafe(32)
    if len(token) < 24:
        parser.error("SNAP_GO_TOKEN must be at least 24 characters")
    try:
        runtime = Runtime(args)
    except (ValueError, OSError, TypeError) as exc:
        parser.error(
            f"Invalid persisted calibration; fix or restore configuration: {exc}"
        )
    server = Server((args.host, args.port), handler(runtime, token))

    def shutdown(signum, frame):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    runtime.start()
    print(
        f"Snap_Go {__version__} | {'SIMULATION — no hardware' if args.simulate else 'HARDWARE'} | http://{args.host}:{args.port}",
        flush=True,
    )
    if not os.getenv("SNAP_GO_TOKEN"):
        print(f"Access token (this run only): {token}", flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        runtime.close()
        server.server_close()


if __name__ == "__main__":
    main()
