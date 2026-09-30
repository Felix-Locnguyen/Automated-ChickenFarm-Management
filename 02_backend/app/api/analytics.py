from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/analytics/summary")
def get_farm_summary(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_farm_summary()

@router.get("/analytics/sensor-history")
def get_sensor_history(device_id: int = None, hours: int = 24, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_sensor_history(device_id=device_id, hours=hours)

@router.get("/analytics/alert-stats")
def get_alert_stats(days: int = 7, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_alert_stats(days=days)

@router.get("/analytics/dashboard")
def get_dashboard_data(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    summary = service.get_farm_summary()
    recent_alerts = service.get_alert_stats(days=1)
    return {
        "summary": summary,
        "recent_alerts": recent_alerts
    }
