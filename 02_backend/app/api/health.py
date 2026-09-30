from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.health.record import HealthRecord
from .schemas import HealthRecordCreate, HealthRecordResponse

router = APIRouter()

@router.get("/health", response_model=list[HealthRecordResponse])
def get_health_records(flock_id: int = None, db: Session = Depends(get_db)):
    query = db.query(HealthRecord)
    if flock_id:
        query = query.filter(HealthRecord.flock_id == flock_id)
    return query.order_by(HealthRecord.created_at.desc()).all()

@router.post("/health", response_model=HealthRecordResponse)
def create_health_record(record: HealthRecordCreate, db: Session = Depends(get_db)):
    db_record = HealthRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/health/{record_id}", response_model=HealthRecordResponse)
def get_health_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    return record

@router.put("/health/{record_id}", response_model=HealthRecordResponse)
def update_health_record(record_id: int, record: HealthRecordCreate, db: Session = Depends(get_db)):
    db_record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Health record not found")
    for key, value in record.dict().items():
        setattr(db_record, key, value)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/health/{record_id}")
def delete_health_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    db.delete(record)
    db.commit()
    return {"message": "Da xoa"}
