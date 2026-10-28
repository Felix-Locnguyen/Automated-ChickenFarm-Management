# 🐔 Automated Chicken Farm Management

## 1. Tên dự án & Giới thiệu

**Automated Chicken Farm Management** — hệ thống **giám sát & điều khiển trang trại gà** tích hợp IoT + AI: theo dõi nhiệt độ/độ ẩm/thức ăn real-time, điều khiển quạt–đèn–máy cho ăn qua web, cảnh báo tự động, ghép thiết bị bằng **QR**, quản lý đa người dùng và **nhận diện gà broiler** bằng YOLO.

**Đối tượng sử dụng:** chủ trại / người chăm gà quy mô nhỏ–vừa; quản trị viên trang trại (role `admin`).

---

## 2. Lý do chọn đề tài

- Chăm sóc gà quy mô hàng nghìn con theo kiểu **quan sát tay** tốn công, dễ trễ phát hiện sự cố (41°C lúc 2h sáng = tổn thất đàn thật sự).
- Cảnh báo phải đến **ngay lập tức** trên điện thoại/máy tính, không phải đợi người tới chuồng.
- Thiết bị IoT thêm vào trại phải **đơn giản**: không cần dây nối PC — dán mã QR là xong.
- AI giúp **giám sát 24/7** tổ gà qua camera: phát hiện mật độ/bệnh → tự báo, thay vì người canh từng phút.

Khi hoàn thành, dự án mang lại: tự động hóa cho ăn + điều hòa khí hậu, cảnh báo sớm giảm tổn thất, quản lý nhiều chuồng/nhiều người dùng trên 1 giao diện, và dữ liệu lịch sử phục vụ quyết định nuôi.

---

## 3. Sơ đồ kiến trúc & nguyên lý hoạt động

```
┌─────────────────────┐   MQTT (1883)    ┌──────────────────────────────────┐
│  ESP32-CAM /        │ ───────────────► │        BACKEND — FastAPI         │
│  simulator          │  farm/sensor/+   │  · JWT auth (farmer/admin)       │
│  (08_scripts/       │  farm/device/+/  │  · CRUD: chuồng, thiết bị, cho   │
│   simulate_esp32cam)│     status       │    ăn, tài chính, sức khỏe       │
└─────────────────────┘                  │  · Alert engine (ngưỡng, anti-   │
        │  ảnh JPEG                      │    spam) + QR pairing            │
        ▼  POST /camera/snapshot         │  · Phân quyền theo owner (B7)    │
┌─────────────────────┐   HTTP           │  · Uplink worker → MQTT          │
│  yolo-service       │ ◄──────────────► └───────────────┬──────────────────┘
│  (FastAPI + YOLO26) │  POST /detect                    │ REST /api/* (JWT)
│  port 8030          │ ─────────────────► bbox + conf   ▼
└─────────────────────┘                  ┌──────────────────────────────────┐
                                         │  FRONTEND — React 18 + Vite      │
   MinIO (khi có Docker) ◄── ảnh bệnh ── │  · Dashboard, Chuồng, Thiết bị, │
   (fallback: /storage/camera local)     │    Cho ăn, Tài chính             │
                                         │  · QR pairing (jsQR), toast B9   │
                                         │  · Polling 10s cảm biến/cảnh báo│
                                         └──────────────────────────────────┘
```

**Luồng dữ liệu (Input → Xử lý → Output):**

1. **Thu thập:** cảm biến gửi reading qua MQTT (`farm/sensor/+`) hoặc HTTP `POST /api/sensor`; camera chụp ảnh định kỳ → `POST /api/camera/snapshot`.
2. **Xử lý trung tâm:** backend ghi `sensor_readings` → `check_reading_and_alert` so với ngưỡng → tạo `alerts` (chống lặp: 1 loại chưa resolve thì không tạo thêm); ảnh được đẩy sang `yolo-service` chạy YOLO26 (`best.pt`) → nếu phát hiện gà → lưu `disease_detections` (bbox + confidence) + tạo alert `type=camera`; ảnh **bình thường bị discard**.
3. **Đầu ra:** web poll mỗi 10s → Dashboard hiển thị reading/ảnh mới nhất; alert mới → **toast `⚠️` + badge 🔔** (B9); người dùng **bật/tắt thiết bị** trên web → `PUT /devices/{id}/toggle` → publish MQTT `farm/device/{id}/command`; thêm thiết bị → hiện **mã QR** → quét/bấm link `?token=` để ghép vào chuồng (B6–B8, B10).

---

## 4. Cấu trúc thư mục *(thư mục đánh số theo phase)*

```
Automated-ChickenFarm-Management/
├── 01_frontend/                 # Web React 18 + Vite 5
│   └── 02_src/
│       ├── App.jsx              # Gốc: auth, tab, adapter backend→UI, B9 toast
│       ├── 02_components/       # 02.1_Dashboard, 02.2_Farm, 02.3_Financial...
│       ├── 03_pages/            # LoginPage, Dashboard, Farm, Devices
│       └── 04_services/         # api.js (REST), auth.js (JWT), websocket.js
│
├── 02_backend/                  # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── main.py              # Entry: mount routers, startup schedulers
│   │   ├── config.py            # Đọc .env (DATABASE_URL, MQTT, YOLO, MINIO)
│   │   ├── api/                 # auth, records, devices, alerts, sensor,
│   │   │                        # feeding, health, financial, camera, analytics
│   │   ├── core/authz.py        # B7: is_admin, get_owned_flock/device (404 che giấu)
│   │   ├── core/security.py     # bcrypt + JWT
│   │   ├── models/              # user, flock, device, sensor/, alert/,
│   │   │                        # feeding/, health/, financial/, disease_detection
│   │   ├── iot/                 # mqtt/connection, command/executor, uplink
│   │   ├── services/            # alert.py, feeding_scheduler, climate_control
│   │   └── storage/             # MinIO client (fallback ảnh local)
│   └── .env                     # Biến môi trường (KHÔNG commit)
│
├── 03_iot/                      # Firmware/đồ họa thiết bị nhúng (ESP32-CAM)
├── 04_machine_learning/
│   └── training/chicken_detection/   # Pipeline 10 module: data→train→eval→report
│       └── runs/{yolo26n,yolo26s}/weights/best.pt
├── 05_docker/                   # docker-compose (minio...) + Dockerfile.*(viết sẵn, CHƯA test — chưa có Docker)
├── 06_docs/                     # Tài liệu chi tiết
├── 07_tests/                    # pytest: models/services/api/workflow/camera/pairing/authorization
├── 08_scripts/                  # seed/data.py, simulate_esp32cam.py, minio_init.py...
├── 09_chatbot/                  # (tương lai) LLM-RAG
├── cloud/yolo-service/          # Service AI riêng: FastAPI POST /detect + Dockerfile
├── runs/, weights/              # Kết quả train YOLO
├── requirements.txt             # Python deps (root)
└── Project-Plan.md              # Kế hoạch + tiến độ sống của dự án
```

---

## 5. Cơ sở dữ liệu & dữ liệu huấn luyện

### 5.1 Bảng dữ liệu (SQLite dev / Postgres khi deploy)

| Bảng | Trường quan trọng | Mô tả |
|---|---|---|
| `users` | `email`, `hashed_password` (bcrypt), `full_name`, `role` | `farmer` (mặc định) / `admin` (thấy toàn hệ thống) |
| `flocks` | `name`, `chicken_count`, `breed`, `age_weeks`, **`owner_id`** | Đàn gà/chuồng — **phân quyền B7**: mỗi user chỉ thấy đàn của mình |
| `devices` | `name`, `type` (fan/light/camera/feeder/sensor), `is_active`, `flock_id`, **`pairing_code`** (6 ký tự unique), `paired_at` | Thiết bị IoT; `flock_id=NULL` = chưa ghép (vô chủ) |
| `sensor_readings` | `temperature`, `humidity`, `food_level`, `water_level`, `device_id`, `created_at` | Dữ liệu cảm biến (MQTT/HTTP uplink) |
| `alerts` | `type`, `severity`, `message`, `flock_id`, `is_resolved` | Cảnh báo vượt ngưỡng / camera; gắn chuồng → chỉ chủ thấy |
| `feeding_logs` | `feed_type`, `amount_kg`, `scheduled_time`, `status`, `flock_id` | Lịch cho ăn; scheduler hoàn thành tự động |
| `health_records` | `record_type`, `description`, `veterinarian`, `flock_id` | Tiêm phòng, khám bệnh |
| `financial_records` | `category` (ban_ga/ban_trung/ga_chet/thuc_an), `revenue`, `total_cost`, `profit`... | Backend tự tính doanh thu/lợi nhuận từ input |
| `disease_detections` | `img_url` (MinIO/local), `detections` (JSON: bbox, conf, cls), `n_detection` | Kết quả YOLO mỗi lần chụp; ảnh bình thường **không lưu** |

### 5.2 Dữ liệu huấn luyện AI (nhận diện gà broiler)

- **Nguồn:** bộ `Chicken.v2-wideangle_yewon_v2` (Roboflow), **120 / 5 / 5** ảnh (train/val/test), nhãn **polygon → chuyển bbox** YOLO; báo cáo `data_report.csv` + fig01–05.
- **Huấn luyện:** `yolo26n` & `yolo26s` (augmentation động: xám/đèn ấm/nhiễu), early-stop — nano mAP50 ≈ **0.923**, small ≈ **0.910**; benchmark test thủ công: small F1 ≈ 0.914 (~75 FPS GPU).
- **Sử dụng:** `cloud/yolo-service` nạp `best.pt` — nhận ảnh base64 → trả `[{bbox, conf, cls}]`; backend lưu + vẽ bbox trên web.
- *Phạm vi:* hiện chỉ nhận diện **gà/bộ phận gà** (phát hiện mật độ tổ); **phát hiện bệnh cụ thể — hoãn** (cần dataset chuyên ngành).

---

## 6. Cài đặt & cấu hình

### 6.1 Yêu cầu hệ thống

| Phần mềm | Phiên bản | Ghi chú |
|---|---|---|
| Python | 3.10+ (dev hiện tại: 3.14) | backend + ML |
| Node.js | 18+ | frontend (npm) |
| Mosquitto (MQTT broker) | chạy localhost:1883 | cho toggle thiết bị + uplink cảm biến |
| Docker | *(chưa cài trên máy dev)* | MinIO/deploy Phase 5 — **chưa test**, ảnh đang lưu local |

### 6.2 Các bước cài đặt

```bash
# 1. Clone
git clone <https://github.com/Felix-Locnguyen/Automated-ChickenFarm-Management.git> && cd Automated-ChickenFarm-Management

# 2. Backend: venv + thư viện
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install "qrcode[pil]"          # sinh QR pairing (đã cài sẵn trong .venv dev)

# 3. Frontend: thư viện JS
cd 01_frontend && npm install                 # react, vite, jsqr (quét QR)
cd ..

# 4. Biến môi trường — 02_backend/.env (xem 02_backend/app/config.py)
```

Biến môi trường chính (`02_backend/.env`):

```dotenv
DATABASE_URL=sqlite:///./farm.db        # dev; prod: postgresql+psycopg2://...
SECRET_KEY=dev-secret-key               # ký JWT — ĐỔI khi deploy
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
YOLO_SERVICE_URL=http://localhost:8030  # service AI (không chạy thì box bệnh tự ẩn)
PAIR_BASE_URL=http://localhost:5173     # URL nhúng vào QR ghép thiết bị
MINIO_ENDPOINT=localhost:9000           # chỉ dùng khi có Docker
```

> ⚠️ **Bài học đường dẫn SQLite (xem Project-Plan.md mục 7):** `sqlite:///./farm.db` là đường dẫn **tương đối theo thư mục chạy uvicorn**. Muốn chắc chắn đúng file thì dùng `realpath`:

```bash
DATABASE_URL="sqlite:///$(realpath ../test_farm.db)"
```

---

## 7. Cách chạy & dùng thử

### 7.1 Khởi chạy hệ thống

```bash
# Terminal 1 — MQTT broker (cần cho điều khiển thiết bị)
mosquitto -p 1883          # hoặc: docker run -p 1883:1883 eclipse-mosquitto

# Terminal 2 — Backend (port 8020; 8000 có thể bị project khác chiếm)
cd 02_backend
DATABASE_URL="sqlite:///./farm.db" ../.venv/bin/uvicorn app.main:app --port 8020

# Terminal 3 — Frontend (proxy /api → 8020, đã cấu hình sẵn trong vite.config.js)
cd 01_frontend && npm run dev              # → http://localhost:5173

# (Tùy chọn) Terminal 4 — AI service cho box "Phát hiện bệnh"
cd cloud/yolo-service && ../../.venv/bin/uvicorn main:app --port 8030

# (Tùy chọn) Terminal 5 — Giả lập ESP32-CAM (không cần phần cứng)
.venv/bin/python 08_scripts/simulate_esp32cam.py
```

**Nạp dữ liệu mẫu** (tạo `admin@farm.vn` + 3 chuồng/12 thiết bị/cảnh báo...):

```bash
cd 02_backend
DATABASE_URL="sqlite:///$(realpath ../farm.db)" ../.venv/bin/python ../08_scripts/seed/data.py
# Script từ chối chạy khi DB đã có user — muốn seed lại thì xóa file DB trước
```

**Chạy test:** `.venv/bin/python -m pytest 07_tests -q` → **38/38 pass** *(test tự dùng `test_farm.db` ở gốc repo, tự xóa tạo lại mỗi session)*.

### 7.2 Tài khoản mẫu

**DB seed** (`02_backend/farm.db` — dữ liệu mẫu đầy đủ, admin thấy tất cả):

| Email | Mật khẩu | Vai trò |
|---|---|---|
| `admin@farm.vn` | `admin123` | admin |

**DB test** (`test_farm.db` ở gốc — do pytest tạo, có sẵn thiết bị chưa ghép cho demo QR):

| Email | Mật khẩu | Vai trò |
|---|---|---|
| `a@gmail.com` | `matkhau123` | farmer (có sẵn 1 chuồng) |
| `b@gmail.com` | `matkhau123` | farmer (trống — dùng để test "không thấy chuồng của a") |
| `admin@gmail.com` | `matkhau123` | admin |

> Muốn web dùng `test_farm.db`: chạy backend với `DATABASE_URL="sqlite:///$(realpath ../test_farm.db)"` (từ `02_backend`).

### 7.3 Các bước thao tác chính trên Web

1. **Đăng nhập** tại `http://localhost:5173` (card đăng nhập — Gmail làm ví dụ email).
2. **Dashboard:** nhiệt độ/độ ẩm/thức ăn poll 10s; **alert mới → toast `⚠️` + badge 🔔**; 🔔 mở danh sách alert → "Đã xử lý".
3. **Chuồng:** thêm/sửa/xóa đàn gà (owner tự động lấy từ token); chi tiết chuồng xem cảm biến, **lịch cho ăn (nhập giờ + lượng kg)**, mức cảnh báo *(lưu tạm trên máy)*.
4. **Thiết bị:** **＋ Thêm thiết bị** (tên/loại/chuồng hoặc *Chưa gán — ghép QR sau*) → **modal QR tự mở** → bấm link `?token=` hoặc **📷 Quét QR** (jsQR, fallback nhập 6 ký tự) → thiết bị ghép vào chuồng. Bật/tắt công tắc → lệnh MQTT.
5. **Tài chính:** sổ thu/chi bán gà/trứng/gà chết/thức ăn — hệ thống tự tính doanh thu, lợi nhuận.
6. **Test nhanh cảm biến bằng curl** (sinh alert khi vượt ngưỡng):

```bash
curl -X POST http://localhost:8020/api/sensor -H "Content-Type: application/json" \
  -d '{"temperature": 42, "humidity": 85, "food_level": 50, "water_level": 50}'
```

---

## 📊 Tình trạng dự án & lộ trình *(ngoài cấu trúc 7 mục)*

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0–1 | Nền tảng: FastAPI, JWT, CRUD, MQTT | ✅ |
| 2 | IoT: simulator, feeder/climate scheduler | ✅ |
| 3 | AI: train YOLO, yolo-service, camera snapshot→alert | ✅ (MinIO + tối ưu inference còn nợ) |
| 4 | **QR pairing (B6–B8), phân quyền multi-user (B7), toast alert (B9), form thêm thiết bị (B10)** | ✅ code (E2E ghép QR chờ xác nhận phần cứng) |
| 5 | Docker & Deploy (4 Dockerfile + compose, Alembic, HTTPS) | Testing|
| Tương lai | Live stream WebRTC, mobile app, chatbot LLM-RAG, OTA | Plan|

