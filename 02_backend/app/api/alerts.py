"""Router cảnh báo — cho phép web xem danh sách alert và đánh dấu đã xử lý.

Trả về kèm tên chuồng (coop_name) vì AlertPanel hiển thị trực tiếp,
không muốn frontend phải query thêm 1 vòng /flocks để tra tên.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..database import get_db
from ..models.alert import Alert
from ..models.flock import Flock

router = APIRouter()


@router.get("/alerts")
def get_alerts(resolved: bool = False, db: Session = Depends(get_db)):
    """Danh sách cảnh báo — mặc định chỉ lấy các alert CHƯA xử lý.

    outerjoin: alert không gắn flock nào vẫn phải trả về (không bị mất).
    """
    rows = (
        db.query(Alert, Flock.name)
        .outerjoin(Flock, Alert.flock_id == Flock.id)
        .filter(Alert.is_resolved == resolved)
        .order_by(Alert.created_at.desc())
        .all()
    )
    return [
        {
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "flock_id": alert.flock_id,
            "coop_name": flock_name or "Hệ thống",
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        for alert, flock_name in rows
    ]


@router.put("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Đánh dấu alert đã xử lý (giấu khỏi danh sách mặc định)."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Cảnh báo không tồn tại")
    alert.is_resolved = True
    db.commit()
    return {"message": "Đã đánh dấu xử lý"}
