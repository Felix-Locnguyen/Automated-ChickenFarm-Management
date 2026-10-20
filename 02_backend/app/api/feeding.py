from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.feeding.log import FeedingLog
from .schemas import FeedingLogCreate, FeedingLogResponse



from ..core.security import get_current_user
from ..models.device import Device
from ..iot.command.executor import CommandExecutor
from ..iot.mqtt.connection import mqtt_handler

router = APIRouter()

@router.get("/feeding", response_model=list[FeedingLogResponse])
def get_feeding_logs(flock_id: int = None, db: Session = Depends(get_db)):
    query = db.query(FeedingLog)
    if flock_id:
        query = query.filter(FeedingLog.flock_id == flock_id)
    return query.order_by(FeedingLog.created_at.desc()).all()

@router.post("/feeding", response_model=FeedingLogResponse)
def create_feeding_log(log: FeedingLogCreate, db: Session = Depends(get_db)):
    db_log = FeedingLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.put("/feeding/{log_id}/complete")
def complete_feeding(log_id: int, db: Session = Depends(get_db)):
    log = db.query(FeedingLog).filter(FeedingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log khong ton tai")
    log.status = "completed"
    db.commit()
    return {"message": "Da hoan tat"}

@router.delete("/feeding/{log_id}")
def delete_feeding_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(FeedingLog).filter(FeedingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log khong ton tai")
    db.delete(log)
    db.commit()
    return {"message": "Da xoa"}



@router.post("/feeding/{log_id}/execute")
def execute_feeding_now(
    log_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Người dùng cho ăn trực tiếp bằng web/app — gửi lệnh FEED + đánh completed.
    """
    # kiểm tra dữ liệu lịch cho ăn có tồn tại không
    log = db.query(FeedingLog).filter(FeedingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Lịch cho ăn không tồn tại")
    # kiểm tra chuông có thiết bị cho ăn chưa
    device = db.query(Device).filter(
        Device.flock_id == log.flock_id,
        Device.type == "feeder",
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Chuồng này chưa có máy feeder")
    # Gửi lệnh điều khiển phần cứng qua MQTT:
    executor = CommandExecutor(db, mqtt_handler)
    if not executor.set_feeder_amount(device.id, log.amount_kg):
        raise HTTPException(
            status_code=503,
            detail="Không gửi được lệnh MQTT (broker chưa kết nối?)",
        )

    log.status = "completed"
    db.commit()
    return {"message": f"Đã gửi lệnh cho ăn {log.amount_kg}kg vào feeder '{device.name}'"}