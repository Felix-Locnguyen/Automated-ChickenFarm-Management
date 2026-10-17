"""Các truy vấn thống kê cho dashboard.

Tách logic truy vấn ra khỏi router (api/analytics.py chỉ gọi service):
- Router lo phần HTTP (nhận request, trả response)
- Service lo phần nghiệp vụ + query DB
→ Dễ test, dễ dùng lại, dễ đọc.
"""
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.alert import Alert
from ..models.flock import Flock
from ..models.sensor.reading import SensorReading


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_farm_summary(self) -> dict:
        """Tổng quan trang trại: tổng đàn, số cảnh báo đang mở, nhiệt độ/độ ẩm mới nhất."""
        # func.sum / func.count: hàm tổng hợp của SQL (SUM, COUNT) — chạy ngay trong DB
        # .scalar(): trả về giá trị ô đầu tiên; None nếu không có dòng nào → `or 0` để tránh None
        total_chickens = self.db.query(func.sum(Flock.chicken_count)).scalar() or 0
        active_alerts = (
            self.db.query(func.count(Alert.id))
            .filter(Alert.is_resolved == False)  # noqa: E712 — so sánh cột Boolean với literal
            .scalar()
            or 0
        )

        last_reading = (
            self.db.query(SensorReading)
            .order_by(SensorReading.created_at.desc())  # mới nhất trước
            .first()
        )

        return {
            "total_chickens": total_chickens,
            "active_alerts": active_alerts,
            "temperature": last_reading.temperature if last_reading else None,
            "humidity": last_reading.humidity if last_reading else None,
            "food_level": last_reading.food_level if last_reading else None,
            "water_level": last_reading.water_level if last_reading else None,
        }

    def get_sensor_history(self, device_id: int = None, hours: int = 24) -> list[dict]:
        """Lấy readings trong N giờ gần nhất (tùy chọn lọc theo device)."""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(SensorReading).filter(SensorReading.created_at >= since)
        if device_id:
            query = query.filter(SensorReading.device_id == device_id)
        readings = query.order_by(SensorReading.created_at.desc()).all()

        # Trả về list dict thay vì object ORM — vì router không có response_model,
        # FastAPI không tự serialize object SQLAlchemy được → sẽ lỗi khi trả JSON
        return [
            {
                "id": r.id,
                "temperature": r.temperature,
                "humidity": r.humidity,
                "food_level": r.food_level,
                "water_level": r.water_level,
                "device_id": r.device_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in readings
        ]

    def get_alert_stats(self, days: int = 7) -> dict:
        """Đếm cảnh báo theo severity trong N ngày gần nhất."""
        since = datetime.utcnow() - timedelta(days=days)
        rows = (
            self.db.query(Alert.severity, func.count(Alert.id))
            .filter(Alert.created_at >= since)
            .group_by(Alert.severity)  # nhóm: warning mấy cái, critical mấy cái
            .all()
        )
        return {severity: count for severity, count in rows}
