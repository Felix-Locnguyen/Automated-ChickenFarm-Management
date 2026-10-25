# -*- coding: utf-8 -*-
"""
Load YOLO26 best.pt + inference (tách riêng khỏi main.py cho gọn).

Biến môi trường (tùy chọn):
  YOLO_MODEL      — tên model: yolo26s (mặc định, F1 cao nhất) | yolo26n
  YOLO_MODEL_PATH — đường dẫn weight tuyệt đối (dùng trong Docker)
  YOLO_CONF       — ngưỡng confidence (mặc định 0.25)
"""
import os
from pathlib import Path

from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[2]          # = gốc repo (yolo-service → cloud → repo)
MODEL_NAME = os.getenv("YOLO_MODEL", "yolo26s")
DEFAULT_WEIGHTS = (REPO_ROOT / "04_machine_learning" / "models" / "chicken_detection"
                   / "runs" / MODEL_NAME / "weights" / "best.pt")
WEIGHTS = Path(os.getenv("YOLO_MODEL_PATH", DEFAULT_WEIGHTS))
CONF_THR = float(os.getenv("YOLO_CONF", "0.25"))

_yolo = None          # lazy-load: chỉ load khi có request đầu tiên


def _get_model() -> YOLO:
    global _yolo
    if _yolo is None:
        if not WEIGHTS.exists():
            raise FileNotFoundError(f"Thiếu weight: {WEIGHTS}")
        _yolo = YOLO(str(WEIGHTS))
    return _yolo


def is_loaded() -> bool:
    return _yolo is not None


def detect(img) -> list[dict]:
    """
    img: PIL RGB → list dict:
      {"bbox": [x1,y1,x2,y2] pixel, "conf": 0-1, "cls": id, "cls_name": tên lớp}
    """
    r = _get_model().predict(img, conf=CONF_THR, iou=0.5, verbose=False)[0]
    out = []
    if r.boxes is None or not len(r.boxes):
        return out
    for xyxy, conf, cls in zip(r.boxes.xyxy.cpu().numpy(),
                               r.boxes.conf.cpu().numpy(),
                               r.boxes.cls.cpu().numpy()):
        cid = int(cls)
        out.append({
            "bbox": [round(float(x), 1) for x in xyxy],
            "conf": round(float(conf), 3),
            "cls": cid,
            "cls_name": r.names.get(cid, "?"),
        })
    return out
