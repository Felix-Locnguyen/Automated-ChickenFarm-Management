from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.flock import Flock
from .schemas import FlockCreate, FlockResponse

router = APIRouter()


# lấy toàn bộ danh sách các đàn gà (flocks) từ database.
@router.get("/flocks", response_model=list[FlockResponse])
def get_flocks(db: Session = Depends(get_db)):
    return db.query(Flock).all()

# tạo dữ liệu mới trong bảng Flock
@router.post("/flocks", response_model= FlockResponse)
def create_flock(flock: FlockCreate, db: Session = Depends(get_db)):
    db_flock = Flock(**flock.dict())
    db.add(db_flock)
    db.commit()
    db.refresh(db_flock)
    return db_flock

# truy ván dữ liệu từ bảng Flock dựa trên id 
@router.get("/flocks/{flock_id}", response_model= FlockResponse)
def get_flock(flock_id: int , db: Session = Depends(get_db)):
    flock = db.query(Flock).filter(Flock.id == flock_id).first()
    if not flock:
        raise HTTPException(status_code= 404, detail= "Flock không tồn tại" )
    return flock

# cập nhật sự thay đổi của dữ liệu
@router.put("/flocks/{flock_id}", response_model=FlockResponse)
def update_flock(flock_id: int, flock: FlockCreate, db: Session = Depends(get_db)):
    db_flock = db.query(Flock).filter(Flock.id == flock_id).first()
    if not db_flock:
        raise HTTPException(status_code=404, detail="Flock không tồn tại")
    for key, value in flock.dict().items():
        setattr(db_flock, key, value) # cập nhật dữ liệu mới từ request vào object db_flock đang có trong database.
    db.commit()
    db.refresh(db_flock)
    return db_flock

# api xóa dữ liệu 
@router.delete("/flocks/{flock_id}")
def delete_flock(flock_id:int , db: Session = Depends(get_db)):
    db_flock = db.query(Flock).filter(Flock.id == flock_id).first()
    if not db_flock:
        raise HTTPException(Status_code= 404, detail="Flock không tồn tại")
    db.delete(db_flock)
    db.commit()
    return {"message": "Đã xóa"}


