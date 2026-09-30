from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Flock(Base):
    __tablename__ = "flocks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    chicken_count = Column(Integer, default=0)
    breed = Column(String(100))
    age_weeks = Column(Integer)
    coop_number = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="flocks")
    devices = relationship("Device", back_populates="flock")
    feeding_logs = relationship("FeedingLog", back_populates="flock")
    health_records = relationship("HealthRecord", back_populates="flock")
    alerts = relationship("Alert", back_populates="flock")
