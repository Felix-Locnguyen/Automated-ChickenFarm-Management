"""Scheduler tự cho ăn theo lịch (FeedingLog.scheduled_time).

Cứ mỗi CHECK_INTERVAL giây:
  - Lấy thời gian hiện tại dạng "HH:MM"
  - Tìm log status="pending" có scheduled_time khớp giờ hiện tại
  - Với mỗi log: tìm máy feeder (type="feeder") của CÙNG chuồng
    → gửi lệnh FEED qua MQTT → đánh dấu completed
    (status chuyển completed → mỗi log chỉ chạy 1 lần — chống lặp tự nhiên)

Chạy như asyncio task trong lifespan của main.py.
"""

import asyncio
import logging
from datetime import datetime

from app.database import SessionLocal
from app.iot.command.executor import CommandExecutor
from app.iot.mqtt.connection import mqtt_handler
from app.models.device import Device
from app.models.feeding.log import FeedingLog


logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 30  # mỗi phút có ít nhất 2 lượt kiểm tra → không lọt phút nào  

def _execute_due_feeds() -> int:
    """Quét log đến giờ cho ăn — chạy trong thread của asyncio.to_thread.

    Hàm này BLOCKING (query DB) nên KHÔNG được gọi thẳng trong event loop
    (sẽ chặn mọi request khác) — caller phải bọc asyncio.to_thread().
    """
    now_hm = datetime.now().strftime("%H:%M")
    db = SessionLocal() # session riêng của scheduler - không dùng chung với request
    try: 
        due_logs = db.query(FeedingLog).filter(
            FeedingLog.status == "pending",
            FeedingLog.scheduled_time == now_hm, # đúng giờ hẹn là cho ăn 
        ).all()
        executed = 0
        for log in due_logs:
            # Tìm máy feeder thuộc cùng chuồng
            device = db.query(Device).filter(
                Device.flock_id == log.flock_id,
                Device.type == "feeder",
            ).first()
            if not device:
                logger.warning(
                    f"Log #{log.id}: chuồng {log.flock_id} chưa có máy feeder — bỏ qua"
                )
                continue

            executor = CommandExecutor(db, mqtt_handler)
            if executor.set_feeder_amount(device.id, log.amount_kg):
                log.status = "completed"
                db.commit()
                executed += 1
                logger.info(
                    f"Cho ăn tự động: {log.amount_kg}kg ({log.feed_type}) "
                    f"→ feeder '{device.name}' — log #{log.id} completed"
                )
        return executed
    finally:
        db.close()




async def _loop():
    "Vòng lặp nền - CHECK_INTERVAL_SECONDS rồi quét dữ liệu 1 lượt"
    logger.info(f"Feeding scheduler đã chạy (kiểm tra mỗi {CHECK_INTERVAL_SECONDS}s)")
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        try:
            # Bọc asyncio.to_thread: query DB là blocking → chạy trong thread
            # pool của event loop, không chặn các request HTTP khác
            await asyncio.to_thread(_execute_due_feeds)
        except Exception as e:  # 1 lỗi lẻ không được giết scheduler
            logger.error(f"Lỗi feeding scheduler: {e}")


_task: asyncio.Task | None = None



def start_scheduler():
    """Gọi trong lifespan startup (async context)."""
    global _task
    _task = asyncio.get_running_loop().create_task(_loop())


async def stop_scheduler():
    """Gọi trong lifespan shutdown — hủy task sạch sẽ."""
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass  # mong đợi khi cancel