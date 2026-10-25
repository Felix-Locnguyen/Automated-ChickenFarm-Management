from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class DiseaseDetection(Base):
    """1 dòng = 1 lần camera snapshot PHÁT HIỆN được đối tượng.

    Hiện tại model nhận diện broiler (Phase 3 theo scope: chỉ gà broiler;
    bệnh/anomaly sẽ có model riêng → thêm cột cls/range sau).
    """
    __tablename__ = "disease_detections"

    id = Column(Integer, primary_key=True, index=True)
    img_url = Column(String(500))          # URL ảnh trên MinIO (None = MinIO chưa sẵn sàng)
    detections = Column(JSON)              # [{bbox, conf, cls, cls_name}, ...]
    conf = Column(Float)                   # confidence cao nhất trong lần chụp
    cls_name = Column(String(50))          # "broiler"
    n_detections = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
