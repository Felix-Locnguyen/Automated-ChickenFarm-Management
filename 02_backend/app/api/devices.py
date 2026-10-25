"""Router thiết bị — tab ⚙️ Thiết bị trên web cần GET /devices + toggle.

Phần "gửi lệnh MQTT xuống thiết bị thật" sẽ nối vào đây ở Phase 2;
hiện tại chỉ quản lý trạng thái trong DB.
"""
import base64
import io
import os
import secrets
from datetime import datetime, timezone
import qrcode

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.authz import get_owned_device, get_owned_flock, is_admin
from ..core.security import get_current_user
from ..database import get_db
from ..models.device import Device
from ..models.flock import Flock
from .schemas import DeviceCreate, DeviceResponse, DeviceConfig, DevicePairRequest



from ..iot.command.executor import CommandExecutor
from ..iot.mqtt.connection import mqtt_handler 


router = APIRouter()

# Base URL của web để ghép chuỗi token vào QR (đổi qua env khi deploy)
PAIR_BASE_URL = os.getenv("PAIR_BASE_URL", "http://localhost:5173")

# Bỏ 0/O/1/I/L — ký tự dễ nhầm khi đọc mã dán trên thiết bị
PAIR_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

# sinh code
def _gen_pairing_code(db: Session) -> str:
    """Sinh code 6 ký tự. secrets = CSPRNG (khó đoán) — không dùng random
    thường, vì đoán được code là ghép được thiết bị của người khác.
    Vòng lặp + unique index: nếu trùng (xác suất rất thấp) thì sinh lại."""
    while True:
        code = "".join(secrets.choice(PAIR_ALPHABET) for _ in range(6))
        if not db.query(Device).filter(Device.pairing_code == code).first():
            return code


def _qr_base64(text: str) -> str:
    """
    Text -> ảnh QR định dạng PNG -> data-URI base64

    data:image/png;base64,... là chuỗi tự chứa — frontend gắn thẳng vào
    <img src={qr_image}> không cần lưu file hay thêm endpoint serve ảnh.
    """

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# =================================================================
@router.get("/devices", response_model=list[DeviceResponse])
def get_devices(flock_id: int = None, db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Danh sách thiết bị — tùy chọn lọc theo chuồng.

    User thấy: thiết bị CHƯA GHÉP (vô chủ, để ghép QR) + thiết bị thuộc chuồng mình.
    Admin thấy tất (B7 owner scoping).
    """
    query = db.query(Device)
    if flock_id:
        query = query.filter(Device.flock_id == flock_id)
    devices = query.order_by(Device.id).all()
    if is_admin(user):
        return devices
    my_flock_ids = [f.id for f in db.query(Flock).filter(Flock.owner_id == user.id)]
    return [d for d in devices if d.flock_id is None or d.flock_id in my_flock_ids]


@router.post("/devices", response_model=DeviceResponse)
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Thêm thiết bị — validate đàn gà phải tồn tại trước (nếu có chọn chuồng).

    flock_id = None → thiết bị chưa thuộc ai, ghép sau bằng QR (/devices/pair).
    """
    if device.flock_id is not None:
        get_owned_flock(db, device.flock_id, user)   # 404 nếu không tồn tại hoặc của người khác
    db_device = Device(**device.dict())
    db_device.pairing_code = _gen_pairing_code(db)
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

    device = get_owned_device(db, device_id, user)   # kiểm quyền TRƯỚC khi chạm MQTT

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
    device = get_owned_device(db, device_id, user)
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

    device = get_owned_device(db, device_id, user)

    executor = CommandExecutor(db, mqtt_handler)
    if not executor.send_command(device_id, "CONFIG", config.config):
        raise HTTPException(
            status_code=503,
            detail="Không gửi được lệnh MQTT (broker chưa kết nối?)",
        )
    return device   # config không đổi trạng thái device → trả về hiện trạng


@router.get("/devices/{device_id}/qr")
def get_device_qr(
    device_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    QR ghép thiết bị. code sinh 1  lần rồi giữ vĩnh viễn - in QR để dán trên thiết bị 
    """

    device = get_owned_device(db, device_id, user)   # vô chủ → xem QR OK; của người khác → 404
    if not device.pairing_code:
        device.pairing_code = _gen_pairing_code(db)
        db.commit()
        db.refresh(device)

    
    pair_url = f"{PAIR_BASE_URL}/?token={device.pairing_code}"
    return {
        "device_id": device.id,
        "pairing_code": device.pairing_code,
        "pair_url": pair_url,
        "qr_image": _qr_base64(pair_url),
    }


@router.post("/devices/pair", response_model=DeviceResponse)
def pair_device(
    payload: DevicePairRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Ghép thiết bị vào trang trại
    """
    device = db.query(Device).filter(Device.pairing_code == payload.pairing_code).first()
    if not device:
        raise HTTPException(status_code=404, detail="Mã QR không đúng")
    if device.flock_id:
        raise HTTPException(status_code= 400, detail="Thiết bị đã được ghép nối trong trại từ trước")
    
    flock = db.query(Flock).filter(Flock.owner_id == user.id).first()
    if not flock:
        raise HTTPException(
            status_code=400,
            detail="Bạn chưa có đàn gà nào — tạo đàn trước khi ghép thiết bị",
        )

    device.flock_id = flock.id
    device.paired_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(device)
    return device