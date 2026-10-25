"""Kiểm tra quyền sở hữu — dùng chung cho các router (B7).

THIẾT KẾ CHE GIẤU: không phân biệt "không tồn tại" vs "không được quyền"
→ cùng trả 404 với 1 câu chung, kẻ xấu không biết resource có thật hay không.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.device import Device
from ..models.flock import Flock
from ..models.user import User

DENIED = {"status_code": 404, "detail": "Không tồn tại hoặc bạn không có quyền"}


def is_admin(user: User) -> bool:
    return user.role == "admin"        # default role là "farmer" (models/user.py)


def get_owned_flock(db: Session, flock_id: int, user: User) -> Flock:
    """Trả flock nếu admin hoặc thuộc về user — sai quyền → 404 che giấu."""
    flock = db.query(Flock).filter(Flock.id == flock_id).first()
    if not flock or (not is_admin(user) and flock.owner_id != user.id):
        raise HTTPException(**DENIED)
    return flock


def get_owned_device(db: Session, device_id: int, user: User) -> Device:
    """Thiết bị CHƯA GHÉP (flock_id=None) = vô chủ → ai cũng thao tác được
    (dòng chảy QR: chưa ai sở hữu thì mới cho ghép). Đã ghép → kiểm chủ chuồng."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(**DENIED)
    if device.flock_id is not None and not is_admin(user):
        flock = db.query(Flock).filter(Flock.id == device.flock_id).first()
        if not flock or flock.owner_id != user.id:
            raise HTTPException(**DENIED)
    return device
