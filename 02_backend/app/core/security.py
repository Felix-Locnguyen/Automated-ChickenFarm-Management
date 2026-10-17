"""Tạo/đọc JWT + hash mật khẩu — trái tim của phần xác thực.

Luồng JWT:
1. Đăng nhập thành công → server ký token bằng SECRET_KEY (client không cần biết secret)
2. Client lưu token, gửi kèm mỗi request:  Authorization: Bearer <token>
3. Server chỉ cần ĐỌC LẠI payload (đã ký nên không ai sửa được) → không cần lưu "session" nào
"""
from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

ALGORITHM = "HS256"  # thuật toán ký JWT

# OAuth2PasswordBearer khai báo "endpoint đăng nhập nằm ở /api/auth/login".
# Khi client gửi header Authorization: Bearer <token>, FastAPI tự tách token ra
# rồi truyền vào tham số `token` của get_current_user.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """Hash mật khẩu bằng bcrypt.

    bcrypt.hashpw trả về bytes → .decode() thành str để lưu vào DB.
    gensalt() sinh "muối" (salt) ngẫu nhiên — mỗi lần hash cùng 1 mật khẩu
    cho ra chuỗi KHÁC nhau → kẻ xấu không dò được bằng bảng tra ngược.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So sánh mật khẩu người dùng nhập với hash trong DB.

    bcrypt.checkpw tự đọc salt nằm bên trong hashed_password để thử lại —
    nên không cần lưu salt riêng.
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    """Tạo JWT: payload + thời hạn + chữ ký."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # "exp" = thời điểm hết hạn (chuẩn JWT)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Dependency bảo vệ route: đọc token → trả về User.

    Cách dùng trong router bất kỳ:
        @router.get("/flocks")
        def list_flocks(db=Depends(get_db), user=Depends(get_current_user)):
            ...
    Token sai / hết hạn / user không tồn tại → tự động trả 401.
    """
    from app.models.user import User  # import trong hàm để tránh circular import

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không xác thực được",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # jwt.decode: xác minh chữ ký (sai secret → ném JWTError) rồi trả payload
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")  # "sub" (subject) = chuẩn JWT — mình lưu user id ở đây
        if sub is None:
            raise credentials_error
        user_id = int(sub)  # sub lưu dạng string (bắt buộc theo chuẩn JWT) → chuyển lại int
    except (JWTError, ValueError):
        raise credentials_error  # token hỏng / sai chữ ký / hết hạn / sub không phải số

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error
    return user
