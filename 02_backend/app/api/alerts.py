"""Router cảnh báo — cho phép web xem danh sách alert và đánh dấu đã xử lý.

Trả về kèm tên chuồng (coop_name) vì AlertPanel hiển thị trực tiếp,
không muốn frontend phải query thêm 1 vòng /flocks để tra tên.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.authz import get_owned_flock, is_admin
from ..core.security import get_current_user
from ..database import get_db
from ..models.alert import Alert
from ..models.flock import Flock

router = APIRouter()


@router.get("/alerts")
def get_alerts(resolved: bool = False, db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """Danh sách cảnh báo — mặc định chỉ lấy alert CHƯA xử lý.

    outerjoin: alert không gắn flock nào vẫn phải trả về (không bị mất).
    Lọc quyền (B7): alert gắn flock → chỉ chủ chuồng (hoặc admin) thấy;
    alert chưa gắn flock (sensor uplink chưa có device — MVP 1 trang trại) → mọi user thấy.
    """
    rows = (
        db.query(Alert, Flock.name, Flock.owner_id)
        .outerjoin(Flock, Alert.flock_id == Flock.id)
        .filter(Alert.is_resolved == resolved)
        .order_by(Alert.created_at.desc())
        .all()
    )
    result = []
    for alert, flock_name, owner_id in rows:
        if alert.flock_id is not None and not is_admin(user) and owner_id != user.id:
            continue                            # alert chuồng người khác → bỏ qua (che giấu)
        result.append({
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "flock_id": alert.flock_id,
            "coop_name": flock_name or "Hệ thống",
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        })
    return result


@router.put("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Đánh dấu alert đã xử lý (giấu khỏi danh sách mặc định)."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    # che giấu 404: không lộ "alert có tồn tại nhưng bạn không được quyền"
    if not alert:
        raise HTTPException(status_code=404, detail="Không tồn tại hoặc bạn không có quyền")
    if alert.flock_id is not None:
        get_owned_flock(db, alert.flock_id, user)   # alert chuồng người khác → 404 che giấu
    # alert chưa gắn flock → mọi user đăng nhập được resolve (như quyền XEM ở trên)
    alert.is_resolved = True
    db.commit()
    return {"message": "Đã đánh dấu xử lý"}
