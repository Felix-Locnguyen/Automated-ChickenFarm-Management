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
from .schemas import DeviceCreate, DeviceResponse, DeviceConfig



from ..iot.command.executor import CommandExecutor
from ..iot.mqtt.connection import mqtt_handler 


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
    """Bật/tắt thiết bị: đảo trạng thái + GỬI LỆNH MQTT xuống phần cứng.

    Quy tắc "không nói dối":
    - executor.toggle_device() chỉ commit DB nếu publish MQTT thành công;
    - broker chết → trả 503, trạng thái DB giữ nguyên (thà báo lỗi còn hơn
      web hiển thị "đã bật" trong khi quạt không quay).
    """

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")
    

    executor = CommandExecutor(db, mqtt_handler) 
    success = executor.toggle_device(device_id) # tính trạng thái mới → send_command() publish → chỉ commit nếu publish OK.

    if not success:
        raise HTTPException(
            status_code=503,
            detail="Không gửi được lệnh MQTT (broker chưa kết nối?) — trạng thái giữ nguyên",
        )

    db.refresh(device)   # executor đã commit → refresh để trả is_active MỚI
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

@router.put("/devices/{device_id}/config", response_model=DeviceResponse)
def configure_device(
    device_id: int,
    config: DeviceConfig,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Gửi cấu hình xuống thiết bị qua MQTT.

    Lưu ý: config không lưu db - chỉ chuyển tới thiết bị
    nếu về sau cần lưu thì thêm cột json vào bảng devices 
    """

    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")

    executor = CommandExecutor(db, mqtt_handler)
    if not executor.send_command(device_id, "CONFIG", config.config):
        raise HTTPException(
            status_code=503,
            detail="Không gửi được lệnh MQTT (broker chưa kết nối?)",
        )
    return device   # config không đổi trạng thái device → trả về hiện trạng