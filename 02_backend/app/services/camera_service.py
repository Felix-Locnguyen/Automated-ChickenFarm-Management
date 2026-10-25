"""Xử lý ảnh snapshot từ camera — gọi từ POST /api/camera/snapshot.

Luồng:  ảnh → yolo-service (B1) → nếu CÓ phát hiện:
            upload MinIO (B2) + lưu bảng disease_detections + tạo alert
         ảnh BÌNH THƯỜNG → DISCARD, không lưu gì
         (★ Nguyên tắc #3 trong Project-Plan)

MinIO chưa cài SDK / chưa chạy → vẫn lưu DB với img_url=None + log cảnh báo
(không crash — test local không cần Docker).
"""
import io
import logging
import time
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models.alert import Alert
from ..models.disease_detection import DiseaseDetection

log = logging.getLogger(__name__)

# Ảnh local (fallback khi MinIO chưa chạy) — main.py mount /storage/camera từ đây
STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage" / "camera"


def detect_image(data: bytes) -> dict | None:
    """Gọi yolo-service `POST /detect` → {"count", "detections"}.

    Trả None nếu service chết/không phản hồi (phần khác tự xử lý).
    """
    try:
        r = httpx.post(
            f"{settings.YOLO_SERVICE_URL}/detect",
            files={"file": ("snapshot.jpg", data, "image/jpeg")},
            timeout=15.0,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("yolo-service không phản hồi (%s)", e)
        return None


def upload_to_minio(data: bytes, object_name: str) -> str | None:
    """Upload ảnh lên MinIO → trả URL public. None nếu thiếu SDK/MinIO (degrade)."""
    try:
        from minio import Minio          # import lười — chưa `pip install minio` thì bỏ qua
    except ImportError:
        log.info("Chưa cài thư viện minio (pip install minio) → bỏ qua upload ảnh")
        return None
    try:
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        client.put_object(
            settings.MINIO_BUCKET, object_name,
            io.BytesIO(data), length=len(data), content_type="image/jpeg",
        )
        scheme = "https" if settings.MINIO_SECURE else "http"
        return f"{scheme}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
    except Exception as e:
        log.warning("Upload MinIO thất bại (%s) — thử lưu local", e)
        return None


def save_image_locally(data: bytes, object_name: str) -> str | None:
    """Fallback khi MinIO chưa có: ghi ảnh vào 02_backend/storage/camera/.

    Trả URL-relative `/storage/camera/<tên>` (frontend đi qua Vite proxy).
    """
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        (STORAGE_DIR / object_name).write_bytes(data)
        return f"/storage/camera/{object_name}"
    except Exception as e:
        log.warning("Không ghi được ảnh local (%s)", e)
        return None


def _has_open_detection_alert(db: Session) -> bool:
    """Chống lặp: snapshot 30s/lần, không được tạo alert dồn dập."""
    return (
        db.query(Alert)
        .filter(Alert.type == "camera", Alert.is_resolved == False)  # noqa: E712
        .first()
        is not None
    )


def process_snapshot(db: Session, data: bytes) -> dict:
    """Toàn bộ pipeline 1 ảnh snapshot. Trả dict có key `status`:
    - "error"    → yolo-service chết (router trả 502)
    - "normal"   → không phát hiện gì → DISCARD
    - "detected" → đã lưu DB (+ ảnh MinIO nếu có) + alert
    """
    result = detect_image(data)
    if result is None:
        return {"status": "error", "detail": "yolo-service không phản hồi"}

    n = int(result.get("count", 0))
    detections = result.get("detections") or []

    if n == 0:
        log.info("Ảnh bình thường (0 phát hiện) → discard, không lưu")
        return {"status": "normal", "count": 0, "saved": False}

    # --- Có phát hiện → lưu ---
    ts = time.strftime("%Y%m%d_%H%M%S")
    object_name = f"broiler_{ts}.jpg"
    img_url = upload_to_minio(data, object_name) or save_image_locally(data, object_name)
    max_conf = max((d.get("conf", 0.0) for d in detections), default=0.0)

    row = DiseaseDetection(
        img_url=img_url,
        detections=detections,
        conf=round(float(max_conf), 3),
        cls_name=detections[0].get("cls_name", "broiler"),
        n_detections=n,
    )
    db.add(row)

    if not _has_open_detection_alert(db):
        db.add(Alert(
            type="camera",
            severity="warning",
            message=f"Camera phát hiện {n} cá thể (conf cao nhất {max_conf:.2f})",
        ))

    db.commit()
    db.refresh(row)
    log.info("Đã lưu detection #%s (%s cá thể, img_url=%s)", row.id, n, img_url)
    return {
        "status": "detected",
        "count": n,
        "saved": True,
        "detection_id": row.id,
        "img_url": img_url,
        "max_conf": row.conf,
    }
