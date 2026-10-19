"""
Singleton MQTTHandler cho app
- Handler giữ kết nối TCP tới broker — mở rồi giữ mãi, KHÔNG mở/close mỗi request.
- main.py start 1 lần khi server boot; các router khác nhau dùng chung 1 instance.

Tại sao KHÔNG khai báo trực tiếp trong main.py?
- Tránh import vòng (router import main → main import router).
- File này không import gì từ app → an toàn import từ bất kỳ đâu.
"""
from .handler import MQTTHandler

# Tạo 1 instance duy nhất
mqtt_handler = MQTTHandler(broker_host="localhost", broker_port=1883)
