# -*- coding: utf-8 -*-
"""
cloud/yolo-service — Service nhận diện gà broiler bằng YOLO26.

  GET  /health  → trạng thái + tên model
  POST /detect  → nhận 1 ảnh (multipart, field "file")
                  trả JSON: [{bbox, conf, cls, cls_name}, ...]

Chạy local (từ thư mục này):
  uvicorn main:app --port 8030
Test:
  curl -F "file=@<đường dẫn ảnh>.jpg" http://127.0.0.1:8030/detect
"""
import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

import model

app = FastAPI(title="YOLO26 Broiler Detection Service", version="1.0")


@app.get("/health")
def health():
    """Kiểm tra service + model đã load chưa."""
    return {"status": "ok", "model": model.MODEL_NAME, "loaded": model.is_loaded()}


@app.post("/detect")
async def detect(file: UploadFile = File(..., description="Ảnh JPG/PNG")):
    """Nhận diện gà trong 1 ảnh → JSON bbox + confidence."""
    data = await file.read()
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")   # chuẩn hóa mọi định dạng → RGB
    except Exception:
        raise HTTPException(status_code=400, detail="File không phải ảnh hợp lệ")
    detections = model.detect(img)
    return {"model": model.MODEL_NAME, "count": len(detections), "detections": detections}
