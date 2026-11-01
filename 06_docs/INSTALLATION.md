# 📦 HƯỚNG DẪN CÀI ĐẶT — Automated Chicken Farm Management

> Viết ngày 31/10/2026 — khớp với trạng thái Phase 5 (Docker local).
> Có 2 cách chạy: **Docker (khuyến nghị)** hoặc **chạy tay từng service (dev)**.

---

## 1. Yêu cầu hệ thống

| Phần mềm | Phiên bản | Ghi chú |
|---|---|---|
| Docker + Compose | Docker ≥ 24, Compose v2 | Cách A — **khuyến nghị** |
| Python | 3.10+ | Cách B (dev) + chạy ML |
| Node.js | 18+ | Cách B (dev) |
| Mosquitto | bản native | Cách B — hoặc `docker run -p 1883:1883 eclipse-mosquitto` |

---

## 2. Cách A — Docker (một lệnh chạy tất cả)

```bash
git clone https://github.com/Felix-Locnguyen/Automated-ChickenFarm-Management.git
cd Automated-ChickenFarm-Management

# Quyền docker (nếu chưa ở group docker — rồi đăng nhập lại)
sudo usermod -aG docker $USER

# Chạy
bash 08_scripts/deploy.sh
```

Script tự động: tạo `05_docker/.env` (bí mật) → build image → `docker compose up` → seed dữ liệu mẫu.

**Sau khi chạy:**

| Thành phần | URL | Tài khoản |
|---|---|---|
| Web app | http://localhost:8080 | `admin@farm.vn` / `admin123` |
| API docs | http://localhost:8020/docs | — |
| MinIO console | http://localhost:9001 | trong `05_docker/.env` |
| Postgres | `localhost:5433` (user `farm`) | trong `05_docker/.env` |
| Mosquitto | `localhost:1884` | không cần pass (dev) |

**Lệnh thường dùng:**

```bash
docker compose -f 05_docker/docker-compose.yml ps            # trạng thái
docker compose -f 05_docker/docker-compose.yml logs -f backend  # log
docker compose -f 05_docker/docker-compose.yml down           # dừng (giữ data volume)
docker compose -f 05_docker/docker-compose.yml down -v        # dừng + XÓA dữ liệu
```

**Cấu trúc container:**

```
frontend (nginx:80) ──proxy /api,/storage──▶ backend (FastAPI:8020)
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        ▼                      ▼                      ▼
                  postgres:5432          mosquitto:1883         yolo-service:8030
                        │                      ▲                      ▲
                        ▼                      │              best.pt (volume ro)
                  minio:9000            thiết bị ESP32 thật
               (bucket disease-images)  trỏ MQTT_HOST = IP máy này, port 1884
```

**Test E2E không cần phần cứng:**

```bash
# Terminal A — giả lập ESP32 cảm biến (MQTT tới container, port host 1884)
# ⚠️ simulator đang hardcode port 1883 — tạm thời dừng mosquitto native
#    (sudo systemctl stop mosquitto) hoặc chạy broker native thay container
.venv/bin/python 08_scripts/iot/simulate_esp32.py --broker localhost

# Terminal B — giả lập ESP32-CAM gửi ảnh
.venv/bin/python 08_scripts/simulate_esp32cam.py --backend http://localhost:8020
```

---

## 3. Cách B — Chạy tay (dev, không Docker)

```bash
# 1. MQTT broker
mosquitto -p 1883          # hoặc: docker run -p 1883:1883 eclipse-mosquitto

# 2. Backend (SQLite cho dev — không cần Postgres)
cd 02_backend
DATABASE_URL="sqlite:///$(realpath ../farm.db)" ../.venv/bin/uvicorn app.main:app --port 8020

# 3. Frontend (vite proxy /api → 8020)
cd 01_frontend && npm install && npm run dev     # → http://localhost:5173

# 4. (Tùy chọn) AI service cho box "Phát hiện bệnh"
cd cloud/yolo-service && ../../.venv/bin/uvicorn main:app --port 8030

# 5. Seed dữ liệu mẫu
cd 02_backend && DATABASE_URL="sqlite:///$(realpath ../farm.db)" ../.venv/bin/python ../08_scripts/seed/data.py
```

> ⚠️ **Bài học SQLite:** `sqlite:///./farm.db` là đường dẫn **tương đối theo thư mục chạy uvicorn** — luôn dùng `realpath` như trên. Chi tiết: `Project-Plan.md` mục 7.

**Chạy test:** `.venv/bin/python -m pytest 07_tests -q` → 38/38 pass.
*(Kill simulator trước khi chạy pytest — node giả lập spam readings làm nhiễu test.)*

---

## 4. Biến môi trường (`02_backend/.env` hoặc `05_docker/.env`)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `DATABASE_URL` | postgres local:5050 | SQLAlchemy URL. Dev SQLite: `sqlite:///$(realpath ../farm.db)` |
| `SECRET_KEY` | dev-secret | Ký JWT — **đổi khi deploy thật** (`openssl rand -hex 32`) |
| `MQTT_BROKER_HOST` / `MQTT_BROKER_PORT` | localhost / 1883 | Trong Docker: `mosquitto` / 1883 |
| `YOLO_SERVICE_URL` | http://localhost:8030 | Không chạy → box bệnh tự ẩn |
| `MINIO_ENDPOINT` | localhost:9000 | Trong Docker: `minio:9000` |
| `PAIR_BASE_URL` | http://localhost:5173 | URL nhúng vào QR ghép thiết bị — Docker dùng `http://localhost:8080` |

---

## 5. Deploy VPS *(chưa làm — plan đợt sau)*

Các bước dự kiến:

1. Cài Docker trên VPS → clone repo → `bash 08_scripts/deploy.sh`
2. Đổi `.env`: `SECRET_KEY` mạnh, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD` thật
3. Mosquitto production: sửa `05_docker/mosquitto.conf` → `allow_anonymous false` + `password_file`, tạo user cho từng ESP32 (`mosquitto_passwd`)
4. Reverse proxy HTTPS: **Caddy** (tự lấy cert) trỏ `domain → :8080`, hoặc nginx + certbot
5. `PAIR_BASE_URL=https://<domain>` để QR trỏ đúng web production
6. Firewall: chỉ mở 80/443; Postgres/Mosquitto/MinIO **không** expose port host (bỏ `ports:` trong compose, hoặc bind `127.0.0.1:`)
7. Backup: volume `pgdata` + `minio-data` (cron + restic/rclone)
