"""Hồ sơ sức khỏe đàn gà (tiêm phòng, khám bệnh...)."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...database import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(100))        # "tiêm phòng", "khám tổng quát"...
    description = Column(String(500))        # mô tả chi tiết
    veterinarian = Column(String(100))       # tên bác sĩ thú y
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # server_default=func.now(): DB tự điền thời điểm INSERT

    flock = relationship("Flock", back_populates="health_records")
