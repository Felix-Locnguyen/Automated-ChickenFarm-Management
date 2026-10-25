from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.authz import get_owned_flock, is_admin
from ..core.security import get_current_user
from ..database import get_db
from ..models.flock import Flock
from .schemas import FlockCreate, FlockResponse

router = APIRouter()


# lấy danh sách đàn gà — CHỈ của mình (admin thấy tất) — B7 owner scoping
@router.get("/flocks", response_model=list[FlockResponse])
def get_flocks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    query = db.query(Flock)
    if not is_admin(user):
        query = query.filter(Flock.owner_id == user.id)
    return query.all()

# tạo dữ liệu mới trong bảng Flock
@router.post("/flocks", response_model= FlockResponse)
def create_flock(flock: FlockCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # current_user: route này BỊ BẢO VỆ — phải gửi header Authorization: Bearer <token>
    # owner_id lấy từ user đang đăng nhập (không tin dữ liệu client gửi lên)
    db_flock = Flock(**flock.dict(), owner_id=current_user.id)
    db.add(db_flock)
    db.commit()
    db.refresh(db_flock)
    return db_flock

# truy vấn dữ liệu từ bảng Flock theo id — của mình hoặc admin (che giấu 404)
@router.get("/flocks/{flock_id}", response_model= FlockResponse)
def get_flock(flock_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_owned_flock(db, flock_id, user)

# cập nhật sự thay đổi của dữ liệu
@router.put("/flocks/{flock_id}", response_model=FlockResponse)
def update_flock(flock_id: int, flock: FlockCreate, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    db_flock = get_owned_flock(db, flock_id, user)      # 404 nếu không tồn tại hoặc của người khác
    for key, value in flock.dict().items():
        setattr(db_flock, key, value) # cập nhật dữ liệu mới từ request vào object db_flock đang có trong database.
    db.commit()
    db.refresh(db_flock)
    return db_flock

# api xóa dữ liệu 
@router.delete("/flocks/{flock_id}")
def delete_flock(flock_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_flock = get_owned_flock(db, flock_id, user)      # 404 che giấu như trên
    db.delete(db_flock)
    db.commit()
    return {"message": "Đã xóa"}


