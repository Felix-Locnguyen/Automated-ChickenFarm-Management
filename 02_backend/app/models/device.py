from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # fan, light, feeder, camera
    status = Column(String(50), default="offline")  # online, offline, warning
    is_active = Column(Boolean, default=False)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    flock = relationship("Flock", back_populates="devices")
    sensor_readings = relationship("SensorReading", back_populates="device")
    alerts = relationship("Alert", back_populates="device")
