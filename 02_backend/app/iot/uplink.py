"""Uplink: nhận dữ liệu cảm biến từ MQTT → lưu sensor_readings + tự sinh alert.

SƠ ĐỒ DÒNG DỮ LIỆU:
    ESP32 ──publish──▶ broker ──▶ paho THREAD gọi on_sensor_message()
                                       │  (CHỈ ném vào queue — không đụng DB)
                                       ▼
                                 queue.Queue  (thread-safe)
                                       │
                                       ▼
    worker THREAD (viết dưới đây) ── lấy msg ── mở SessionLocal() RIÊNG ── lưu DB

TẠI SAO PHẢI QUEUE? (bài học thread-safety chính của Phase 2)
- paho-mqtt chạy network trong 1 thread riêng; callback chạy TRONG thread đó.
- SQLAlchemy Session KHÔNG thread-safe; session của FastAPI (get_db) sống theo request.
- Nếu callback tự mở Session → 2 thread thao tác DB đồng thời → race condition.
→ Pattern chuẩn: producer (paho thread) chỉ ĐẨY vào queue.Queue,
  consumer (worker thread) tự mở/đóng session của chính nó.
"""

import json 
import logging
import queue
import threading


from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.device import Device
from app.models.sensor.reading import SensorReading
from app.services.alert import check_reading_and_alert



logger = logging.getLogger(__name__)

# Queue thread-safe: producer = thread của paho, consumer = worker thread dưới đây
message_queue: "queue.Queue" = queue.Queue()

_STOP = object()       # "sentinel" — tín hiệu đặc biệt bảo worker thoát vòng lặp
_worker_thread = None  # giữ tham chiếu thread để stop sau này


def on_sensor_message(topic: str, payload: dict):
    """Callback đăng ký cho topic 'farm/sensor/+' — chạy TRONG thread của paho.

    NGUYÊN TẮC VÀNG: hàm này KHÔNG được mở Session hay đụng DB.
    Chỉ đẩy (topic, payload) vào queue rồi trả về ngay.
    """
    message_queue.put((topic, payload))


def _handle_message(db: Session, topic: str, payload: dict):
    """Xử lý 1 message cảm biến — chạy trong worker thread, có session riêng truyền vào."""
    # Topic dạng "farm/sensor/{device_id}" → tách device_id
    parts = topic.split("/")          # ["farm", "sensor", "1"]
    try:
        device_id = int(parts[2])
    except (IndexError, ValueError):
        logger.warning(f"Topic sai định dạng, bỏ qua: {topic}")
        return

    # Ép kiểu + kiểm tra field bắt buộc — payload hỏng thì bỏ qua, chớ crash
    try:
        reading = SensorReading(
            device_id=device_id,
            temperature=float(payload["temperature"]),
            humidity=float(payload["humidity"]),
            food_level=float(payload["food_level"]),
            water_level=float(payload["water_level"]),
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Payload thiếu/sai field ({topic}): {e} — payload={payload}")
        return

    db.add(reading)
    # Cứ thấy thiết bị gửi dữ liệu là còn sống → đánh dấu online
    device = db.query(Device).filter(Device.id == device_id).first()
    if device:
        device.status = "online"
    db.commit()
    db.refresh(reading)

    # Tự sinh alert nếu vượt ngưỡng — DÙNG LẠI logic đã có từ Phase 1
    new_alerts = check_reading_and_alert(db, reading)
    logger.info(
        f"Uplink OK: device={device_id} temp={reading.temperature} hum={reading.humidity} "
        f"→ {len(new_alerts)} alert mới"
    )


def _worker_loop():
    """Worker thread: lặp mãi lấy message từ queue rồi lưu DB.

    SessionLocal() ở đây là session RIÊNG của worker — không dùng chung
    với request của FastAPI → an toàn thread.
    """
    db = SessionLocal()
    try:
        while True:
            item = message_queue.get()   # blocking — chưa có msg thì ngủ tại đây
            if item is _STOP:            # nhận tín hiệu dừng từ stop_worker()
                break
            topic, payload = item
            try:
                _handle_message(db, topic, payload)
            except Exception as e:       # 1 lỗi lẻ không được giết chết worker
                db.rollback()
                logger.error(f"Lỗi xử lý message {topic}: {e}")
    finally:
        db.close()


def start_worker():
    """Start worker thread — gọi 1 lần ở startup (main.py lifespan).

    daemon=True: nếu process chết bất thường, thread tự bị thu hồi
    (không giữ chương trình sống dai).
    """
    global _worker_thread
    _worker_thread = threading.Thread(target=_worker_loop, name="mqtt-uplink", daemon=True)
    _worker_thread.start()
    logger.info("Uplink worker đã chạy (thread nền)")


def stop_worker():
    """Dừng worker — gọi 1 lần ở shutdown. Đưa sentinel vào queue để worker thoát sạch."""
    if _worker_thread and _worker_thread.is_alive():
        message_queue.put(_STOP)
        _worker_thread.join(timeout=5)   # chờ tối đa 5s cho thread đóng session + thoát