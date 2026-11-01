"""
Singleton MQTTHandler cho app
- Handler giữ kết nối TCP tới broker — mở rồi giữ mãi, KHÔNG mở/close mỗi request.
- main.py start 1 lần khi server boot; các router khác nhau dùng chung 1 instance.

Tại sao KHÔNG khai báo trực tiếp trong main.py?
- Tránh import vòng (router import main → main import router).
- File này chỉ import từ app.config (không import router) → an toàn import từ bất kỳ đâu.
"""
from app.config import settings
from .handler import MQTTHandler

# Tạo 1 instance duy nhất — đọc host/port từ .env (MQTT_BROKER_HOST/PORT).
# Docker: broker tên service "mosquitto"; dev local: localhost — đổi qua .env.
mqtt_handler = MQTTHandler(
    broker_host=settings.MQTT_BROKER_HOST,
    broker_port=settings.MQTT_BROKER_PORT,
)
