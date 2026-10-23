# 🗺️ PROJECT PLAN — Trang Trại Gà Thông Minh (Automated Chicken Farm Management)

> Roadmap xây dựng dự án — viết để bám theo khi phát triển.
> Tài liệu tham chiếu kèm theo: `bao-cao-frontend.md`, `bao-cao-backend.md` (báo cáo hiện trạng code).

---

## 1. Tầm nhìn & Phạm vi

Xây dựng hệ thống **quản lý trang trại gà tự động hóa**, gồm:

| Chức năng | Mô tả |
|---|---|
| 🍽️ Cho ăn tự động, **định lượng** | Người dùng đặt "cho 500g" → thiết bị rải đủ lượng đã đặt rồi tự dừng (có cảm biến cân) |
| 💧 Cho uống tự động, **định lượng** | Tương tự cho ăn — đo lưu lượng/nước rồi dừng |
| 🌡️ Kiểm tra nhiệt độ, độ ẩm | Cảm biến đo liên tục, vượt ngưỡng thì báo alert |
| 💡 Đèn sưởi | Bật/tắt từ web (relay) — tự bật khi nhiệt độ xuống thấp |
| 🌀 Quạt giảm độ ẩm | Bật/tắt từ web (relay) — tự bật khi độ ẩm cao |
| 📷 Camera nhận diện bệnh | Ảnh được gửi lên **cloud**, model AI (YOLO) nhận diện — **chỉ lưu ảnh gà bị bệnh**, không lưu ảnh gà bình thường |
| 📷 Camera quan sát tổ | Người dùng xem được từ bất cứ đâu qua **kết nối internet** (snapshot định kỳ) |
| 🔗 Kết nối thiết bị qua **QR** | Mỗi thiết bị có QR dán sẵn — quét trên web là ghép vào trang trại |
| 🐔 Quản lý đàn gà & tài chính | CRUD đàn, sổ thu/chi, thống kê (đã có nền tảng sẵn) |

**Tạm dừng (phase sau):** Chatbot LLM-RAG (Ollama/ChromaDB) — để ở Phase tương lai, chưa đụng tới.

---

## 2. Kiến trúc tổng thể

```
┌────────────────────────────── TRANG TRẠI (nội bộ) ──────────────────────────────┐
│                                                                                 │
│  ┌─────────────┐   WiFi    ┌────────────────┐                                  │
│  │  ESP32-CAM  │──────────▶│  MQTT Broker   │                                  │
│  │ (camera)    │  ảnh/JPEG │  (Mosquitto)   │                                  │
│  └─────────────┘           └───────┬────────┘                                  │
│  ┌─────────────┐                   │ dữ liệu cảm biến + trạng thái             │
│  │    ESP32    │───────────────────┤ (uplink)                                  │
│  │ cảm biến    │                   │                                            │
│  │ nhiệt/ẩm    │◀──────────────────┤ lệnh ON/OFF/SET_AMOUNT (downlink)         │
│  │ + relay     │                   │                                            │
│  │ quạt/đèn/   │          ┌────────┴────────┐                                  │
│  │ máyn ăn/uống│          │    BACKEND      │                                  │
│  └─────────────┘          │   (FastAPI)     │                                  │
│                           └────────┬────────┘                                  │
└────────────────────────────────────┼───────────────────────────────────────────┘
                                     │ HTTPS (internet)
        ┌────────────────────────────┼──────────────────────────┐
        │ CLOUD (VPS + Docker)       │                          │
        │  ┌──────────┐  ┌───────────▼──┐  ┌─────────┐  ┌──────▼─────┐
        │  │ Postgres │  │    YOLO      │  │  MinIO  │  │  WEB APP   │
        │  │ (DB)     │  │   Service    │  │(ảnh bệnh)│  │  (React)   │
        │  └──────────┘  │nhận diện bệnh│  └─────────┘  └────────────┘
        │                └──────────────┘   ↑ CHỈ lưu ảnh gà bệnh
        │                Web xem snapshot ← ảnh chụp định kỳ
        └────────────────────────────────────────────────────────┘
```

**Quy tắc quan trọng:** Ảnh từ camera **chỉ được xử lý và lưu khi model xác định có gà bị bệnh**. Ảnh bình thường → xử lý xong là bỏ, không lưu (tiết kiệm dung lượng + tôn trọng dữ liệu).

---

## 3. Các Phase phát triển

> Quy ước: mỗi phase có **Danh sách task** (checkbox để tick dần) và **Tiêu chí hoàn thành** (Definition of Done — DoD).

### ✅ PHASE 0 — Khôi phục nền tảng backend (ƯU TIÊN SỐ 1)

*Mục tiêu: code backend đang "chết" (thiếu main.py/database.py) → chạy được, kết nối được DB.*

- [x] Viết `02_backend/app/database.py` — engine Postgres, `Base`, `get_db()`
- [x] Viết `02_backend/app/config.py` — đọc `.env` (DB_URL, MQTT_URL, SECRET_KEY, MINIO_*)
- [x] Tạo file `.env.example` (mẫu) + file `.env` local
- [x] Viết `02_backend/app/main.py` — khởi tạo FastAPI, `include_router` tất cả router với prefix `/api`, CORS, startup/shutdown MQTT
- [x] Bổ sung 3 model còn thiếu: `models/feeding/log.py`, `models/health/record.py`, `models/financial/record.py`
- [x] Bổ sung `services/analytics_service.py` (dùng trong `analytics.py`)
- [x] Thêm `__init__.py` còn thiếu: `app/`, `app/iot/`, `app/models/sensor/`, `models/feeding/`, `models/health/`
- [x] Import `financial` vào `api/__init__.py`
- [x] Fix bug `Status_code` → `status_code` trong `api/records.py` (lỗi 404)
- [x] Thêm `response_model` cho `GET /sensors/latest` (tránh lỗi serialize)
- [x] Sửa `requiment.txt` → `requirements.txt` chuẩn (thêm `paho-mqtt`, `bcrypt`, `python-jose`, `pytest`, `httpx`; xóa lệnh shell lẫn lộn)
- [x] Viết script seed dữ liệu mẫu `08_scripts/seed/data.py` (admin@farm.vn / admin123, 3 đàn, thiết bị, readings...)
- [x] Tạo test cơ bản `07_tests/` (pytest + TestClient, 21 test) — thay file rỗng
- [x] Viết login thật: `POST /auth/login` + **JWT** + hash mật khẩu bằng `bcrypt` (thay plaintext)
- [x] Thêm dependency `get_current_user` bảo vệ các route cần đăng nhập (`POST /flocks`)
- [x] Dọn `.gitignore` (bản cũ 23.790 dòng, ignore nhầm main.py/config.py/database.py)

**Bug phát hiện & fix thêm trong lúc test:**
- [x] JWT `sub` phải là string theo chuẩn → `str(user.id)` khi tạo token, `int()` khi đọc
- [x] `POST /flocks` không gán `owner_id` → lỗi validate → lấy từ token JWT
- [x] `financial.py`: khấu hao gà chết tính theo `unit_price` (giá bán) → sửa thành `cost_per_chick` (giá mua — gà chết là lỗ vốn mua)
- [x] `SensorReading` `device_id` nullable → schema response/create cũng phải Optional

**DoD:** `uvicorn app.main:app` chạy được; mở `/docs` thấy toàn bộ API; đăng ký + đăng nhập trả về JWT hoạt động; dữ liệu lưu/đọc được (đã verify bằng SQLite, 21/21 test pass — Postgres chưa cài trên máy, sang Phase 5 sẽ có Docker).

---

### 🎯 PHASE 1 — Core CRUD hoạt động thật (bỏ mock data ở frontend)

*Mục tiêu: 5 tab trên web dùng dữ liệu thật từ DB.*

- [x] Đồng bộ tên endpoint frontend ↔ backend (hiện `api.js` gọi `/api/coops` nhưng backend dùng `/flocks`)
- [x] Thêm proxy `/api` vào `01_frontend/vite.config.js`
- [x] Viết `04_services/api.js` đầy đủ: auth (login/register + lưu token), flocks, sensors, feeding, health, financial, analytics
- [x] Gắn token `Authorization: Bearer` vào mọi request
- [x] Sửa `App.jsx`: xóa mock data → fetch từ API khi app mở
- [x] Tab 🐔 Quản lý gà: dùng `/flocks` (thay `coops` mock) — gồm cả thêm/sửa/xóa chuồng trên web
- [x] Tab ⚙️ Thiết bị: CRUD `/devices` (router `api/devices.py` + toggle từ web)
- [x] Tab 💵 Tài chính: dùng `/financial` (CRUD đầy đủ, tự trừ/cong số gà khi bán/gà chết)
- [x] Tab 📊 Quản lí TC: groupby 7 ngày/30 ngày/12 tháng — tính client-side từ `/financial` (số liệu thật; endpoint `/financial/summary` đã có sẵn nếu cần)
- [x] Tab 🏠 Dashboard: số liệu thật — compose từ `/flocks` + `/alerts` + `/sensors/latest` (endpoint `/analytics/dashboard` đã có sẵn)
- [x] Viết router `api/alerts.py` (list, resolve) + logic tạo alert tự động khi cảm biến vượt ngưỡng (`services/alert.py` — có chống lặp alert đang mở)
- [x] Viết `LoginPage.jsx` gọi API thật thay `users.js` hard-code
- [x] Lưu JWT vào `localStorage` (đăng nhập qua F5)
- [x] Dọn các file mồ côi: `Records.jsx`, `Settings.jsx` + 3 component placeholder `02.3_Records/` (đã xóa — không được trang nào dùng)

**DoD:** ✅ Đạt — thêm/sửa/xóa đàn gà + phiếu thu/chi trên web → lưu DB thật; dashboard số liệu thật; không còn hard-code; alert tự sinh khi cảm biến vượt ngưỡng (25/25 test pass, frontend build OK).
**Test tay còn lại:** checklist 7 bước trên browser (tạo alert thật qua `/docs` → thấy trên 🔔).

---

### ⚡ PHASE 2 — IoT thật: ESP32 + MQTT + thiết bị cho ăn/uống định lượng

*Mục tiêu: điều khiển được thiết bị thật trong chuồng từ web.*

*Tiến độ (21/10): **xong Bước 0-9 — backend IoT Phase 2 ĐÓNG** (test tổng E2E 7/7: uplink/alert/downlink/CONFIG/cho ăn thủ công/climate auto/scheduler tự động + 25 pytest pass). Đã commit+push: `b52d0c1` (Bước A), `dae6f01` (fix start_worker trùng + crash simulator), `25efcf7` (viết lại 3 chức năng A3 simulator). Còn chờ: phần cứng (board ESP32 → flash farm_node.ino + hiệu chuẩn HX711) + test tay trên browser. Lưu ý khi test: chạy pytest phải kill simulator trước (node spam readings làm nhiễu test).* 

- [ ] Dựng thư mục firmware `03_iot/` (ESP32 — Arduino/PlatformIO): WiFi + MQTT client *(20/10: đã viết `farm_node.ino` — DHT22 + HC-SR04 + HX711 + 3 relay, đúng protocol backend; sketch HC-SR04 cũ → `practice_hcsr04.ino`; còn thiếu: biên dịch/flash thật khi có board + hiệu chuẩn HX711)*
- [ ] Cảm biến nhiệt độ/độ ẩm (DHT22/SHT31) → publish JSON định kỳ lên topic `farm/sensor/{device_id}` *(protocol JSON đã chuẩn — backend nhận & lưu test OK; chờ phần cứng)*
- [x] Xử lý **uplink** trong backend: `iot/mqtt/handler.py` subscribe topic cảm biến → lưu `sensor_readings` *(Bước 3 — `app/iot/uplink.py`: subscribe `farm/sensor/+` → queue → worker thread tự mở Session — thread-safe; kèm tự sinh alert)*
- [x] Nối `CommandExecutor` vào REST: viết `PUT /devices/{id}/toggle`, `PUT /devices/{id}/config` *(Bước A1 — `/config` nhận dict → publish `CONFIG` + params; test pass 21/10: ear thấy lệnh + simulator in `⚙️` — nhánh CONFIG từng gỡ ở `081295e`, đã viết lại ở `25efcf7`)*
- [x] Relay khiển **đèn sưởi** + **quạt** (ON/OFF qua topic `farm/device/{id}/command`) *(Bước 4-6 — backend publish đầy đủ, test pass bằng `mosquitto_sub`; chờ relay thật)*
- [ ] **Máy cho ăn định lượng**: motor + **load-cell** (HX711) — lệnh `FEED` `{amount_kg}` → quay motor, cân realtime, dừng khi đủ *(backend Bước 5 đã gửi lệnh + scheduler; còn phần cứng)*
- [ ] **Máy uống định lượng**: tương tự (van nước + cảm biến lưu lượng / bơm + cân)
- [x] Cập nhật firmware báo lại trạng thái thực (đã cho ăn xong, số gram thực, lỗi kẹt motor) *(Bước A2 — `farm_node.ino` publish `farm/device/{id}/status`; backend subscribe `farm/device/+/status` → worker xử lý: lỗi → device `warning` + alert feeding critical chống lặp, xong → `online`; test E2E pass 21/10 — simulator báo status done đầy đủ, phần này từng gỡ ở `081295e` rồi viết lại ở `25efcf7`)*
- [x] Backend lưu "lịch cho ăn" (`feeding_logs`) → tới giờ tự publish lệnh (`asyncio` task trong main.py) *(Bước 5 — `services/feeding_scheduler.py` quét mỗi 30s + endpoint `POST /feeding/{id}/execute`; test pass)*
- [x] Tự động hóa: nhiệt độ/ẩm vượt ngưỡng → tự bật quạt; nhiệt < ngưỡng → tự bật đèn sưởi; **có tắt/bật chế độ auto** *(Bước 6 — `services/climate_control.py` quét mỗi 10s + `GET/PUT /api/environment/auto`; mặc định TẮT khi boot)*
- [x] Test bench: giả lập ESP32 bằng script Python publish MQTT để test không cần phần cứng *(Bước 7 — `08_scripts/iot/simulate_esp32.py`: publish readings xoay kịch bản + nhận lệnh ON/OFF/FEED, motor mô phỏng trong thread riêng; review PASS. 21/10: đủ 4 chức năng — readings + ON/OFF/FEED + CONFIG + báo status + cờ `--no-sensor` (A3 từng gỡ ở `081295e`, tự code lại ở `25efcf7`, E2E pass))*

**DoD:** Bấm công tắc trên web → quạt/đèn/ESP32 thật bật tắt; đặt "cho ăn 500g" → máy rải đúng 500g rồi dừng; cảm biến hiện số liệu realtime trên dashboard; vượt ngưỡng → có alert.
*(21/10: phần software ĐẠT — test tổng E2E 7/7 pass bằng simulator, 25 pytest; các vế "thật" (ESP32/relay/motor thật) chờ phần cứng.)*

---

### 📷 PHASE 3 — Camera & AI trên Cloud (nhận diện bệnh)

*Mục tiêu: ảnh camera → cloud → YOLO → chỉ ảnh bệnh được lưu & hiển thị.*

**ML nội bộ — Nhận diện broiler (local, trước khi tích hợp cloud):**
- [x] Chuẩn bị dataset `Chicken.v2-wideangle_yewon_v2` + GĐ1 kiểm tra/xử lý (polygon→bbox, 120/5/5 mẫu, `data_report.csv` + fig01-05)
- [x] GĐ2 — xem trước augmentation động: xám / đèn ấm / nhiễu (fig13)
- [x] GĐ3 — train **yolo26n** + **yolo26s** (8.2 phút, early-stop; nano: mAP50=0.923 / mAP50-95=0.659, small: 0.910 / 0.657)
- [x] Refactor `pipeline.py` → 10 module (config/encoding/data_check/data_process/features/viz/training/evaluation/report) — commit `a64d549`
- [x] GĐ4 — benchmark test set thủ công (`--stage eval` → `validation_report.md`: IoU-variants, P/R/F1/mAP, CM, speed, complexity) *(23/10: nano F1=0.903/mAP50=0.889, small F1=0.914/mAP50=0.914 — small nhỉnh hơn trên test 5 ảnh; ~75 FPS GPU)*

- [ ] Dựng `cloud/yolo-service/` (Docker): FastAPI nhỏ nhận ảnh, chạy YOLOv8 `best.pt` (model đã có trong `04_machine_learning/`)
- [x] Viết script xuất model YOLO → `best.pt` dùng được *(23/10: đã train — `training/chicken_detection/runs/{yolo26n,yolo26s}/weights/best.pt`)*
- [ ] Cài MinIO (S3-compatible) qua docker-compose để lưu **ảnh bệnh**
- [ ] ESP32-CAM: chụp ảnh định kỳ (vd 30–60s) → POST lên backend `/api/camera/snapshot`
- [ ] Backend: nhận ảnh → gửi sang `yolo-service` inference → nếu **phát hiện bệnh**:
  - [ ] Lưu ảnh + bbox + nhãn bệnh + confidence vào MinIO + DB (`disease_detections` table — tạo model mới)
  - [ ] Tạo alert tương ứng
  - [ ] Nếu bình thường: **không lưu gì** (log discard là xong)
- [ ] Camera quan sát tổ: snapshot lưu vòng tròn (vd giữ 24h, xóa cũ) để người dùng xem từ web
- [ ] Frontend: hiện snapshot mới nhất (refresh tự động qua polling `/api/camera/latest`)
- [ ] Frontend: component "Phát hiện bệnh" dùng data thật (`DiseaseDetectionBox.jsx` đã có sẵn UI) — hiển thị **ảnh thật** thay placeholder `🖼️ Ảnh model AI (Chưa tích hợp model)`
- [ ] Xem chi tiết từng phát hiện: ảnh + bbox + thời gian + confidence
- [ ] Tối ưu: resize ảnh trước khi inference, rate-limit, chỉ giữ ảnh bệnh N ngày (cleanup job)

**DoD:** Camera chụp → ảnh bệnh xuất hiện trên Dashboard kèm ảnh; ảnh bình thường không xuất hiện trong DB/MinIO; xem được ảnh camera từ trình duyệt ở bất kỳ đâu có internet.

---

### 🔗 PHASE 4 — Kết nối thiết bị qua QR + hoàn thiện UX

*Mục tiêu: người dùng tự thêm được thiết bị/chuồng bằng cách quét QR.*

- [ ] Backend: mỗi device/coop sinh `pairing_code` duy nhất (token)
- [ ] API: `POST /devices/pair` (nhập token) + `GET /devices/{id}/qr`
- [ ] QR chứa URL dạng `https://<ten-web>/pair?token=xxx`
- [ ] Dán/nhãn QR lên thiết bị vật lý khi đóng gói
- [ ] Web: trang `/pair` — quét QR (dùng thư viện jsQR/react-qr-reader) → thiết bị tự ghép vào trang trại của user
- [ ] Chia quyền: multi-user — mỗi user chỉ thấy trang trại/chuồng của mình (`owner_id` đã có sẵn trong model Flock)
- [ ] Phân quyền `farmer` / `admin` (cột role đã có sẵn, chưa dùng)
- [ ] Thông báo cảnh báo nổi (toast + badge) khi có alert mới (polling hoặc WebSocket backend — `04_services/websocket.js` đã viết sẵn wrapper)
- [ ] Nâng giao diện: sửa nốt UI placeholder còn dang dở

**DoD:** Quét QR → thiết bị/thuộc chuồng của đúng người dùng; user A không thấy chuồng của user B; có QR thật để in dán thiết bị.

---

### 🐳 PHASE 5 — Đóng gói Docker & Deploy test

*Mục tiêu: một lệnh `docker compose up` là cả hệ thống chạy.*

- [ ] Viết `05_docker/Dockerfile.backend` (hiện file rỗng)
- [ ] Viết `05_docker/Dockerfile.frontend` (build Vite → nginx)
- [ ] Viết `05_docker/Dockerfile.nginx` (reverse proxy: `/api` → backend, `/` → web)
- [ ] Viết `05_docker/Dockerfile.yolo` (yolo-service)
- [ ] Viết `05_docker/docker-compose.yml` gồm các service:
  `postgres`, `mosquitto` (MQTT), `minio`, `backend`, `yolo-service`, `frontend/nginx`
- [ ] Cấu hình Mosquitto: topic auth, lưu retained message nếu cần
- [ ] Script migrate DB khi khởi động (Alembic — cấu hình lần đầu)
- [ ] Ghi `06_docs/INSTALLATION.md` (đang rỗng): hướng dẫn cài local + deploy VPS
- [ ] Deploy thử lên VPS (Docker Compose), cấu hình domain + HTTPS (Caddy/nginx + certbot)
- [ ] Viết checklist test E2E: đăng ký → thêm chuồng → ghép thiết bị QR → cảm biến hoạt động → cho ăn định lượng → kích hoạt giả lập bệnh → thấy ảnh bệnh trên dashboard → xem tài chính
- [ ] Viết `08_scripts/deploy.sh` (đang rỗng)

**DoD:** `docker compose up` trên VPS sạch → toàn bộ hệ thống hoạt động qua HTTPS; checklist E2E pass.

---

### 🚀 PHASE TƯƠNG LAI (chưa làm — chỉ ghi ở đây)

- **Chatbot LLM-RAG** (Ollama + ChromaDB + LangChain, dữ liệu mard.gov.vn) — theo `LLM-RAG-RoadMap.md`
- **Live stream WebRTC** cho camera (thay snapshot) — dùng MediaMTX/mediasoup
- Ứng dụng **mobile** (React Native/Flutter) để quét QR tiện hơn
- **OTA update** firmware từ xa
- Dự báo giá gà/thị trường bằng ML

---

## 4. Thứ tự thực hiện & ước lượng

| # | Phase | Độ khó | Phụ thuộc | Ghi chú |
|---|---|---|---|---|
| 0 | Khôi phục backend | ⭐⭐ | — | **Làm trước tiên**, mọi thứ khác dựa vào đây |
| 1 | Core CRUD + nối frontend | ⭐⭐ | Phase 0 | Web hoạt động với data thật |
| 2 | IoT (ESP32 + MQTT + định lượng) | ⭐⭐⭐ | Phase 1 | Cần phần cứng để test thật |
| 3 | Camera + AI cloud (YOLO + MinIO) | ⭐⭐⭐⭐ | Phase 1–2 | Model YOLO đã có sẵn |
| 4 | QR pairing + phân quyền | ⭐⭐ | Phase 2 | |
| 5 | Docker + Deploy | ⭐⭐ | Phase 1 (tối thiểu) | Có thể song song từ Phase 2 |

> 💡 Mẹo: Phase 5 (Docker) có thể làm sớm ngay sau Phase 1 để môi trường dev/deploy thống nhất, không cần đợi đến cuối.

---

## 5. Ghi chú kỹ thuật / Bẫy đã phát hiện (đừng quên fix)

| Vấn đề | Vị trí |
|---|---|
| Thiếu `main.py`, `database.py`, `config.py` → backend không chạy được | `02_backend/app/` |
| Thiếu 3 model: `feeding/log.py`, `health/record.py`, `financial/record.py` | `02_backend/app/models/` |
| Router `financial` không được import | `02_backend/app/api/__init__.py` |
| Bug `Status_code=` (hoa S) → NameError | `02_backend/app/api/records.py` |
| `requiment.txt` sai chính tả, thiếu thư viện, lẫn lệnh shell | gốc repo |
| Mật khẩu lưu plaintext | `02_backend/app/api/auth.py` |
| Frontend gọi endpoint không tồn tại (`/api/coops`...) | `01_frontend/02_src/04_services/api.js` |
| Chưa có proxy `/api` trong Vite | `01_frontend/vite.config.js` |
| Auth hash SHA-256 + user hard-code ở client | `04_services/auth.js`, `users.js` |
| File rỗng 0 byte: `05_docker/*`, `07_tests/*`, `08_scripts/deploy.sh`, `08_scripts/setup/db.py` | cần viết lại |
| paho-mqtt chưa set `callback_api_version` (lỗi khi nâng paho 2.x) | `iot/01_mqtt/handler.py` |

---

## 6. Nguyên tắc phát triển

1. **Phase 0 là nền móng** — không code feature mới khi backend còn chưa chạy được.
2. **Ưu tiên chạy thật với DB** — bỏ dần mock data, mỗi task kết thúc phải có thể test tay được.
3. **Chỉ lưu ảnh bệnh** — mọi pipeline ảnh phải có bước "bình thường → discard".
4. **Mỗi task một commit** — message rõ ràng theo conventional commit (đã làm được từ Phase 2: `feat(iot):...`, `fix:...`; trước đó toàn "upload code").
5. **Cập nhật tài liệu** — khi đổi endpoint, sửa `bao-cao-*.md` và `06_docs/` theo.

---

*Cập nhật lần đầu: 16/10/2026. Cập nhật gần nhất: 23/10/2026 (Phase 3 — ML nội bộ **hoàn thành cả 4 giai đoạn** (dataset→train→eval, validation_report.md); tiếp theo: tích hợp cloud). Tài liệu này sống — sửa dần khi dự án tiến triển.*
