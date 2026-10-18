"""Router thiết bị — tab ⚙️ Thiết bị trên web cần GET /devices + toggle.

Phần "gửi lệnh MQTT xuống thiết bị thật" sẽ nối vào đây ở Phase 2;
hiện tại chỉ quản lý trạng thái trong DB.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..database import get_db
from ..models.device import Device
from ..models.flock import Flock
from .schemas import DeviceCreate, DeviceResponse

router = APIRouter()


@router.get("/devices", response_model=list[DeviceResponse])
def get_devices(flock_id: int = None, db: Session = Depends(get_db)):
    """Danh sách thiết bị — tùy chọn lọc theo chuồng."""
    query = db.query(Device)
    if flock_id:
        query = query.filter(Device.flock_id == flock_id)
    return query.order_by(Device.id).all()


@router.post("/devices", response_model=DeviceResponse)
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Thêm thiết bị — validate đàn gà phải tồn tại trước."""
    flock = db.query(Flock).filter(Flock.id == device.flock_id).first()
    if not flock:
        raise HTTPException(status_code=404, detail="Chuồng không tồn tại")
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.put("/devices/{device_id}/toggle", response_model=DeviceResponse)
def toggle_device(
    device_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Bật/tắt thiết bị: đảo trạng thái is_active + cập nhật status.

    Phase 2 sẽ thêm: publish lệnh MQTT xuống phần cứng ở đây —
    nếu thiết bị thật xác nhận thì mới commit (tránh báo thành công giả).
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")
    device.is_active = not device.is_active
    device.status = "online" if device.is_active else "offline"
    db.commit()
    db.refresh(device)
    return device


@router.delete("/devices/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")
    db.delete(device)
    db.commit()
    return {"message": "Đã xóa"}
