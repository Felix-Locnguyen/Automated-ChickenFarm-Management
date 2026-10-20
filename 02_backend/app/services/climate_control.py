"""
Cảm biến đo kiểm soát nhiệt độ môi trường của chuồng
Tự động hóa môi trường chuồng: đọc cảm biến - bật / tắt quạt và đèn sưởi cho gà 

Nguyên lí hoạt động (mỗi 10s  hệ thống sẽ thực hiện các task sau với điểu kiện chức năng auto được bật)
    - Lấy dữ liệu mới nhất của từng chuồng 
    - so sánh dữ liệu mới với DEFAULT_THRESHOLDS (cảnh báo mặc định của hệ thống)
        ví dụ:
            temperature > 35°C  → BẬT quạt      (nóng → thông gió)
            temperature < 20°C  → BẬT đèn sưởi  (lạnh → sưởi ấm)
            humidity    > 80%   → BẬT quạt      (ẩm → phòng bệnh hô hấp)
            còn lại             → TẮT cả hai

    - Chỉ publish MQTT cho thiết bị whose state ĐỔI — không spam lệnh.

CHẾ ĐỘ AUTO:
  - PUT /api/environment/auto {"enabled": true/false}
  - TẮT: scheduler không đụng thiết bị → người dùng điều khiển tay (Bước 4).
  - BẬT: backend quyết định — bấm tay sẽ bị giành lại ở lượt quét sau.
"""


import asyncio
import logging  # Công cụ ghi nhật ký hoạt động và theo dõi lỗi của hệ thống

from app.database import SessionLocal
from app.iot.command.executor import CommandExecutor
from app.iot.mqtt.connection import mqtt_handler
from app.models.device import Device
from app.models.sensor.reading import SensorReading
from app.services.alert import DEFAULT_THRESHOLDS


logger = logging.getLogger(__name__)
CHECK_INTERVAL_SECONDS = 10 


# in-memory, reset về False khi restart server — CỐ Ý: server boot
# không bật thiết bị thật cho tới khi người dùng chủ động bật auto
_auto_enabled = False
_task: asyncio.Task | None = None

# kiểm tra người dùng có bật chế độ auto không
def is_auto_enabled() -> bool:
    return _auto_enabled

# nhận thông tin khi người dùng ấn vào
def set_auto(enabled: bool) -> bool:
    global _auto_enabled
    _auto_enabled = bool(enabled)
    logger.info(f"Chế độ tự động hoá môi trường: {'BẬT' if _auto_enabled else 'TẮT'}")
    return _auto_enabled

def _latest_reading_per_flock(db) -> dict[int,SensorReading]:
    """
    Ghi nhận dữ liệu mới nhất của từng chuồng - dict{flock_id: reading}.
    
    Đảo ngược SensorReading.device_id -> device.flock_id để gom theo chuồng 
    """
    latest: dict[int, SensorReading] = {}
    readings = (
        db.query(SensorReading)
        .order_by(SensorReading.created_at.desc())   # mới nhất trước
        .limit(500)                                   # giới hạn an toàn
        .all()
    )

    for r in readings:
        if not r.device:
            continue
        flock_id = r.device.flock_id
        if flock_id is None or flock_id in latest:
            continue

        latest[flock_id] = r  # đọc dữ liệu có id mới nhất

    return latest




def _set_device_state(db, device: Device, target_on: bool) -> None:
    """
    Đưa thiết bị về trạng thái mong muốn, chỉ publish nếu TRẠNG THÁI ĐỔI.
    """
    if bool(device.is_active) == target_on:
        return # đã đúng → không publish, không commit (tránh spam MQTT)

    command = "ON" if target_on else "OFF"
    executor = CommandExecutor(db, mqtt_handler)
    if executor.send_command(device.id, command):
        device.is_active = target_on
        device.status = "online" if target_on else "offline"
        db.commit()
        logger.info(f"AUTO: {device.name} (id={device.id}) → {command}")
    else:
        logger.warning(f"AUTO: không gửi được lệnh {command} cho {device.name}")


def _tick():
    """Một lượt quét — blocking (query DB) → chạy trong asyncio.to_thread."""
    db = SessionLocal()
    try:
        latest = _latest_reading_per_flock(db)
        for flock_id, reading in latest.items():
            t = DEFAULT_THRESHOLDS
            need_fan = reading.temperature > t["temp_max"] or reading.humidity > t["hum_max"]
            need_light = reading.temperature < t["temp_min"]

            devices = db.query(Device).filter(Device.flock_id == flock_id).all()
            for device in devices:
                if device.type == "fan":
                    _set_device_state(db, device, need_fan)
                elif device.type == "light":
                    _set_device_state(db, device, need_light)
    finally:
        db.close()



async def _loop():
    """
    vòng lặp nền - mỗi check interval second sẽ quét 1 lượt với điều kiện người dùng bật chết độ auto
    """

    logger.info(
        f"Climate control scheduler đã chạy (kiểm tra mỗi {CHECK_INTERVAL_SECONDS}s, "
        f"auto={'BẬT' if _auto_enabled else 'TẮT'})"
    )
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        if not _auto_enabled:
            continue   # auto TẮT → bỏ qua, KHÔNG đụng thiết bị
        try:
            await asyncio.to_thread(_tick)
        except Exception as e:
            logger.error(f"Lỗi climate scheduler: {e}")



def start_climate():
    """gọi trong lifespan """
    global _task
    _task = asyncio.get_running_loop().create_task(_loop())


async def stop_climate():
    """Gọi trong lifespan shutdown"""
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass



