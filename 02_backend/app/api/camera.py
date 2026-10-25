"""Router camera — nhận ảnh snapshot từ ESP32-CAM (hoặc script giả lập B5).

  POST /camera/snapshot — 1 ảnh → yolo-service → CHỈ LƯU khi có phát hiện
  GET  /camera/latest   — lần phát hiện gần nhất (frontend polling ~10s)

Chưa cần auth (giống uplink cảm biến Phase 2) — phân quyền để Phase 4 (QR).
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.disease_detection import DiseaseDetection
from ..services.camera_service import process_snapshot

router = APIRouter()

MAX_SIZE = 5 * 1024 * 1024     # 5MB — chặn ảnh "quá to" làm phình RAM


@router.post("/camera/snapshot")
async def camera_snapshot(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Nhận 1 ảnh → detect → chỉ lưu khi có phát hiện."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng")
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Ảnh quá lớn (>5MB)")

    result = process_snapshot(db, data)
    if result["status"] == "error":
        raise HTTPException(status_code=502, detail=result["detail"])
    return result


@router.get("/camera/latest")
def camera_latest(db: Session = Depends(get_db)):
    """Lần phát hiện gần nhất — `detection: null` nếu chưa từng phát hiện."""
    row = db.query(DiseaseDetection).order_by(DiseaseDetection.id.desc()).first()
    if row is None:
        return {"detection": None}
    return {
        "detection": {
            "id": row.id,
            "img_url": row.img_url,
            "detections": row.detections,
            "conf": row.conf,
            "cls_name": row.cls_name,
            "n_detections": row.n_detections,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    }
