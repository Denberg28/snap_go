from __future__ import annotations
from dataclasses import dataclass
from time import monotonic
from .tracking import Detection

@dataclass
class Box:
    x1: float; y1: float; x2: float; y2: float; confidence: float; class_id: int

def select_subject(boxes: list[Box], width: int, height: int, class_id: int = 0, min_conf: float = 0.45) -> Detection | None:
    eligible = [b for b in boxes if b.class_id == class_id and b.confidence >= min_conf]
    if not eligible: return None
    b = max(eligible, key=lambda x: x.confidence * max(1.0,(x.x2-x.x1)*(x.y2-x.y1)))
    return Detection(cx=((b.x1+b.x2)/2)/width, cy=((b.y1+b.y2)/2)/height, confidence=b.confidence, seen_at=monotonic())

class YoloDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        from ultralytics import YOLO
        self.model = YOLO(model_path)
    def detect(self, frame):
        h,w = frame.shape[:2]
        result = self.model.predict(frame, verbose=False)[0]
        boxes=[]
        for b in result.boxes:
            x1,y1,x2,y2 = map(float,b.xyxy[0].tolist())
            boxes.append(Box(x1,y1,x2,y2,float(b.conf[0]),int(b.cls[0])))
        return select_subject(boxes,w,h)
