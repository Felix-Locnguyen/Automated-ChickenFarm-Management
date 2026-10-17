"""Bảng ghi lịch sử / định lịch cho ăn.

Tên trường phải khớp với FeedingLogCreate / FeedingLogResponse trong api/schemas.py
và các router trong api/feeding.py đang truy cập (log.status, ...).
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...database import Base


class FeedingLog(Base):
    __tablename__ = "feeding_logs"

    id = Column(Integer, primary_key=True, index=True)
    feed_type = Column(String(100))           # loại thức ăn: "corn", "pellet"...
    amount_kg = Column(Float)                 # số kg thức ăn
    scheduled_time = Column(String(20))       # giờ hẹn cho ăn (VD "06:30") — string cho đơn giản
    status = Column(String(20), default="pending")  # pending / completed
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationship KHÔNG phải cột trong DB — là helper để viết feeding_log.flock
    # (SQLAlchemy tự query bảng flocks giúp)
    flock = relationship("Flock", back_populates="feeding_logs")
