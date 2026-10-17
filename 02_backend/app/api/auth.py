from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..database import get_db
from ..models.user import User
from .schemas import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản mới — mật khẩu được HASH bằng bcrypt trước khi lưu."""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),  # ← đã hash, không còn plaintext
        full_name=user.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Đăng nhập → trả về JWT token.

    Client lưu token rồi gửi kèm mỗi request:
        Authorization: Bearer <token>
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    # Không nói rõ "sai email" hay "sai mật khẩu" — tránh kẻ xấu dò email có tồn tại
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Sai email hoặc mật khẩu")

    # "sub" (subject) theo chuẩn JWT PHẢI là string → str(user.id),
    # phần get_current_user sẽ tự int() lại
    access_token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
