# 03_iot — Firmware ESP32 cho trang trại

## File

| File | Vai trò |
|---|---|
| `farm_node.ino` | **Firmware chính** — node chuồng gà: DHT22 + HC-SR04 + HX711 + 3 relay, nói MQTT đúng protocol backend (Bước 3-6) |
| `practice_hcsr04.ino` | Bài tập cũ (đo khoảng cách + LCD), để lại để học — **chưa sửa bug cú pháp** |
| `wokwi.toml` + `diagram.json` | Schematic mô phỏng trên Wokwi (VS Code extension) — test không cần board |

## Cài thư viện (Arduino IDE → Tools → Manage Libraries)

```
PubSubClient        (Nick O'Leary)
DHT sensor library  (Adafruit)
HX711 Arduino Library (bogde)
ArduinoJson         (Benoit Blanchon)
LiquidCrystal_I2C   (chỉ cần cho practice_hcsr04.ino)
```

Board: **ESP32 Dev Module** (cài board ESP32 trong Arduino IDE → Preferences → Additional Boards Manager URLs).

## Cấu hình trước khi flash — sửa 3 khối đầu `farm_node.ino`

1. `WIFI_SSID` / `WIFI_PASSWORD` — WiFi 2.4GHz của trang trại (ESP32 **không** thấy WiFi 5GHz)
2. `MQTT_HOST` — **IP máy tính** chạy mosquitto (xem bằng `hostname -I`), KHÔNG ghi "localhost"
3. `SENSOR_ID / FAN_ID / LIGHT_ID / FEEDER_ID` — đúng `id` trong DB:

```bash
curl -s http://localhost:8000/api/devices | python3 -m json.tool
```

## Wiring (sơ đồ dây)

```
ESP32          Thiết bị
GPIO4    ──── DHT22 (data, kèm resistor 10kΩ pull-up)
GPIO5    ──── HC-SR04 TRIG        GPIO18 ──── HC-SR04 ECHO
GPIO25   ──── Relay IN1 (quạt)          GPIO26 ──── Relay IN2 (đèn sưởi)
GPIO27   ──── Relay IN3 (motor cho ăn)
GPIO32   ──── HX711 DOUT          GPIO33 ──── HX711 SCK
3V3/VIN  ──── VCC cảm biến; relay module dùng VIN 5V nếu board hỗ trợ
GND      ──── GND chung TẤT CẢ (nghiêm cấn thiếu — bug số 1 của người mới)
```

> Relay module thường **quán tính LOW = ON** — đã set `RELAY_ON LOW` trong code. Module 5V cần transistor/level-shifter nếu dùng với ESP32 3V3.

## Hiệu chuẩn HX711 (bắt buộc trước khi dùng FEED thật)

1. Tháo hết thức ăn, cấp nguồn → `loadCell.tare()` tự trừ khối lượng khay
2. Đặt vật nặng **đã biết trọng lượng** (vd chai nước 1kg) → xem serial (115200)
3. Sửa `HX711_CALIBRATION` tới khi serial in đúng 1000g

## Test không cần board — Wokwi

- VS Code + extension **Wokwi for VS Code** → mở folder `03_iot/` → F5
- Hoặc wokwi.com — upload `diagram.json` + sketch
- Lưu ý: `wokwi.toml` hiện trỏ firmware build cũ (`DHT22_Sensor_Test`) — nếu build bằng PlatformIO thì đổi tên env cho khớp, hoặc xóa 2 dòng `firmware`/`elf` để Wokwi tự build

## Giao thức MQTT (khớp 100% với backend)

```
📤 farm/sensor/{SENSOR_ID}            mỗi 5s:
   {"temperature":28.5,"humidity":55,"food_level":75,"water_level":80}
📥 farm/device/{FAN_ID}/command       {"command":"ON","device_type":"fan","params":{}}
📥 farm/device/{LIGHT_ID}/command     {"command":"ON",...}
📥 farm/device/{FEEDER_ID}/command    {"command":"FEED","device_type":"feeder","params":{"amount_kg":2.5}}
📤 farm/device/{FEEDER_ID}/status     {"state":"done","actual_grams":2498.0,"target_grams":2500.0}
                                      {"state":"error","error":"ket-motor",...}
```

> Topic `status` backend **chưa subscribe** (Phase sau) — nhưng firmware đã báo sự thật từ đầu.

## Bài học kỹ thuật trong code (đọc comment trong sketch)

1. **State machine + `millis()` thay vì `delay()`** — khi motor đang rải, loop vẫn chạy đều → vẫn nhận MQTT (cùng bài học thread-safety với queue ở uplink backend)
2. **Chống kẹt motor** — cân không tăng trong 15s → dừng motor + báo `error: ket-motor`
3. **MQTT clientId duy nhất** — trùng clientId thì broker "đá" thiết bị này, nối lại thiết bị kia
4. **`tare()` khi silo trống** — nạp gì cũng phải trừ khối lượng khay trước
