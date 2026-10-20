from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.sensor.reading import SensorReading
from ..services.alert import check_reading_and_alert
from .schemas import SensorReadingCreate, SensorReadingResponse,AutoModeUpdate
from ..core.security import get_current_user
from ..services import climate_control

router = APIRouter()

@router.get("/sensor", response_model=list[SensorReadingResponse])

def get_reading(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Hàm get_reading nhận vào:
    # - skip: số bản ghi bỏ qua (mặc định 0)
    # - limit: số bản ghi tối đa trả về (mặc định 100)
    # - db: phiên làm việc với database, được inject tự động nhờ Depends(get_db)

    reading = db.query(SensorReading).order_by(
        SensorReading.created_at.desc()   # Sắp xếp theo thời gian tạo, mới nhất trước
    ).offset(skip).limit(limit).all()     # Bỏ qua 'skip' bản ghi, lấy 'limit' bản ghi

    return reading
    # Trả về danh sách các bản ghi cảm biến (sensor readings) cho client

@router.post("/sensor", response_model= SensorReadingResponse)
def create_reading(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    db_reading = SensorReading(**reading.dict()) # Tạo một object SensorReading mới từ dữ liệu đầu vào (chuyển dict → object SQLAlchemy)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    # Tự sinh cảnh báo nếu reading vượt ngưỡng (temp/ẩm/food/water)
    check_reading_and_alert(db, db_reading)

    return db_reading


@router.get("/sensors/latest", response_model=SensorReadingResponse)
def get_lastest_reading(db: Session = Depends(get_db)):
    reading = db.query(SensorReading).order_by(
        SensorReading.created_at.desc()
    ).first()
    return reading 


'''
Giải thích query:
db.query(SensorReading)          # SELECT * FROM sensor_readings
    .order_by(created_at.desc()) # ORDER BY created_at DESC
    .offset(skip)                # OFFSET 0
    .limit(limit)                # LIMIT 100
    .all()                       # → list of objects
'''


@router.get("/environment/auto")
def get_auto_mode():
    """Xem chế độ tự động hoá đang bật hay tắt."""
    return {"auto_enabled": climate_control.is_auto_enabled()}



@router.put("/environment/auto")
def set_auto_mode(update: AutoModeUpdate, user=Depends(get_current_user)):
    """Bật/tắt chế độ tự động hoá môi trường.

    - BẬT: backend tự bật/tắt quạt + đèn sưởi dựa trên cảm biến (mỗi 10s).
    - TẮT: scheduler đứng yên — người dùng điều khiển tay bình thường.
    """
    climate_control.set_auto(update.enabled)
    return {"auto_enabled": climate_control.is_auto_enabled()}