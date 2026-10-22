# -*- coding: utf-8 -*-
"""
MÃ HÓA nhãn & tọa độ:
  - parse + validate 1 dòng label YOLO
  - polygon → bbox              (chuẩn bị cho train detect)
  - YOLO chuẩn hóa → pixel     (vẽ ảnh, so khớp GT lúc đánh giá)
"""
from config import CLASS_NAMES


def parse_label_line(line):
    """
    Đọc 1 dòng label → (class_id, vals, kind, lỗi):
      - 'bbox'    : 5 cột (class xc yc w h)
      - 'polygon' : ≥10 cột, chẵn (chưa convert)
      - lỗi ≠ ''  : class_id=None → dòng KHÔNG hợp lệ
    Kiểm tra: parse được số, class ∈ CLASS_NAMES, tọa độ ∈ [0,1], w/h > 0.
    """
    parts = line.strip().split()
    if not parts:
        return None, None, "invalid", "dòng rỗng"
    try:
        vals = [float(x) for x in parts[1:]]
        cls_id = int(float(parts[0]))
    except ValueError:
        return None, None, "invalid", "không parse được số"
    if cls_id not in CLASS_NAMES:
        return None, vals, "invalid", f"class_id {cls_id} ngoài danh sách"
    if any(not (0.0 <= v <= 1.0) for v in vals):
        return None, vals, "invalid", "tọa độ nằm ngoài [0,1]"
    if len(vals) == 4:
        if vals[2] <= 0 or vals[3] <= 0:
            return None, vals, "invalid", "width/height <= 0"
        return cls_id, vals, "bbox", ""
    if len(vals) >= 10 and len(vals) % 2 == 0:
        return cls_id, vals, "polygon", ""
    return None, vals, "invalid", f"số cột {len(vals) + 1} không hợp lệ"


def poly_to_bbox(vals):
    """Polygon [x1,y1,x2,y2,…] (0-1) → bbox [xc, yc, w, h]."""
    xs, ys = vals[0::2], vals[1::2]
    x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
    return [round((x1 + x2) / 2, 6), round((y1 + y2) / 2, 6),
            round(x2 - x1, 6), round(y2 - y1, 6)]


def to_yolo_line(cls_id, vals, kind):
    """Dòng label gốc (bbox HOẶC polygon) → 1 dòng YOLO bbox 5 cột (string)."""
    bbox = vals if kind == "bbox" else poly_to_bbox(vals)
    return f"{cls_id} " + " ".join(str(x) for x in bbox)


def yolo_to_xyxy(vals, W, H):
    """bbox YOLO (xc,yc,w,h chuẩn hóa) → (x1, y1, x2, y2) theo pixel."""
    xc, yc, w, h = vals
    return ((xc - w / 2) * W, (yc - h / 2) * H,
            (xc + w / 2) * W, (yc + h / 2) * H)


def load_gt(label_path, W, H):
    """Đọc file nhãn YOLO → [(xyxy_pixel, class_id), …] — GT cho đánh giá."""
    boxes = []
    for line in label_path.read_text().strip().splitlines():
        v = line.split()
        if len(v) >= 5:
            boxes.append((yolo_to_xyxy(list(map(float, v[1:5])), W, H), int(v[0])))
    return boxes
