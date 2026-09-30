from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # temperature, humidity, feeding
    severity = Column(String(50), default="warning")  # warning, critical
    message = Column(String(500))
    is_resolved = Column(Boolean, default=False)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    flock = relationship("Flock", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")