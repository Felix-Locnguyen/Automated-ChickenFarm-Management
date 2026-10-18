"""Entry point của cả backend.

Chạy server (trong thư mục 02_backend):
    uvicorn app.main:app --reload
Mở Swagger để test: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, environment, feeding, financial, health, records, alerts, devices
from app.database import Base, engine
from app.iot import uplink
from app.iot.mqtt.connection import mqtt_handler

# Python mặc định chỉ hiện log WARNING trở lên → bật INFO để thấy
# "Connected to MQTT broker..." khi khởi động server.
logging.basicConfig(level=logging.INFO)

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

    # Startup: kết nối MQTT + start loop nền (thread của paho)
    # .start() dùng loop_start() → paho tự chạy 1 thread network riêng,
    # main thread (uvicorn) không bị chặn.
    try:
        mqtt_handler.connect()   # thử kết nối — fail cũng không crash server
        mqtt_handler.start()
        # Uplink: lắng nghe cảm biến — "+" = 1 cấp bất kỳ
        mqtt_handler.subscribe("farm/sensor/+", uplink.on_sensor_message)
        uplink.start_worker()
    except Exception as e:
        print(f"[MQTT] Không kết nối được broker (sẽ thử lại sau): {e}")

    yield

    # Shutdown: dừng worker trước, ngắt MQTT sau (đúng thứ tự — tránh mất message dở dang)
    uplink.stop_worker()
    mqtt_handler.stop()


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
