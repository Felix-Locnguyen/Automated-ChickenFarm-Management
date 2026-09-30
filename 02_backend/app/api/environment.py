from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.sensor.reading import SensorReading
from .schemas import SensorReadingCreate, SensorReadingResponse

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
    return db_reading


@router.get("/sensors/latest")
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