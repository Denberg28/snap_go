from __future__ import annotations

class OpenCVCamera:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        import cv2
        self.cv2 = cv2
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened(): raise RuntimeError(f"camera {index} failed to open")
    def read(self):
        ok, frame = self.cap.read()
        if not ok: raise RuntimeError("camera frame read failed")
        return frame
    def close(self): self.cap.release()

class CameraDetectionSource:
    def __init__(self, camera, detector): self.camera, self.detector = camera, detector
    def next_detection(self): return self.detector.detect(self.camera.read())
