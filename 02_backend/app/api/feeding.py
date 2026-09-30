from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.feeding.log import FeedingLog
from .schemas import FeedingLogCreate, FeedingLogResponse

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
