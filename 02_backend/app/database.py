"""Kết nối database + định nghĩa Base cho ORM.

Phân vai:
- engine       : "đường ống" kết nối tới PostgreSQL (tạo 1 lần khi import)
- SessionLocal : factory tạo session — mỗi session = 1 "phiên làm việc" với DB
- Base         : lớp gốc, mọi model kế thừa Base để SQLAlchemy biết tạo bảng nào
- get_db       : dependency của FastAPI — cấp 1 session cho mỗi request rồi tự đóng
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# pool_pre_ping=True: trước khi dùng lại kết nối cũ thì "ping" thử 1 lần,
# nếu DB đã ngắt (mạng chập chờn...) thì tự kết nối lại thay vì báo lỗi
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# autocommit=False, autoflush=False: ép mình chủ động commit() — tránh意外 ghi dữ liệu
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency của FastAPI — mỗi request nhận 1 session riêng.

    yield: hàm "generator" — FastAPI hiểu:
      - phần TRƯỚC yield: chạy trước khi vào endpoint
      - phần SAU yield: chạy sau khi endpoint xong (dù có lỗi hay không)
    → đảm bảo db.close() luôn được gọi, tránh rò rỉ kết nối DB.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
