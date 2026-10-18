"""Entry point của cả backend.

Chạy server (trong thư mục 02_backend):
    uvicorn app.main:app --reload
Mở Swagger để test: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, environment, feeding, financial, health, records, alerts, devices
from app.database import Base, engine

# Đã đổi tên thư mục iot ở Phase 2: mqtt/, device/, command/ (bỏ tiền tố số
# vì Python không import được module tên bắt đầu bằng số).


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chạy 1 lần khi START server và 1 lần khi STOP.

    - create_all: tạo các bảng theo model (bảng nào chưa có thì tạo).
      Lưu ý: create_all KHÔNG sửa bảng đã tồn tại — đổi schema thì dùng Alembic.
    - yield là ranh giới: trên = startup, dưới = shutdown.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: Phase 2 sẽ dừng MQTT ở đây (mqtt_handler.stop())


app = FastAPI(
    title="Automated Chicken Farm API",
    description="API quản lý trang trại gà thông minh",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — cho phép trang web (domain khác) gọi API.
# 5173 là cổng mặc định của Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include_router: ghép từng router vào app.
# prefix="/api" → mọi endpoint trong router đều thêm tiền tố /api
# (ví dụ "/auth/login" thành "/api/auth/login")
for router_module in [auth, environment, feeding, records, health, analytics, financial, alerts, devices]:
    app.include_router(router_module.router, prefix="/api")


@app.get("/health")
def health_check():
    """Endpoint kiểm tra "server còn sống không" — dùng cho Docker healthcheck sau này."""
    return {"status": "ok"}
