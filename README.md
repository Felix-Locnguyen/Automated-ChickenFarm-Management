```text
automated-chicken-farm/
│
├── frontend/                      # Ứng dụng web giao diện người dùng
│   ├── public/                    # Tài nguyên tĩnh công khai
│   │   ├── favicon.svg           # Biểu tượng trang web
│   │   └── icons.svg             # Các biểu tượng SVG dùng chung
│   │
│   ├── src/
│   │   ├── assets/               # Hình ảnh, CSS, fonts - các tài nguyên giao diện
│   │   │
│   │   ├── components/           # Các thành phần React tái sử dụng
│   │   │   ├── Dashboard/        # Bảng điều khiển chính
│   │   │   │   ├── EnvironmentMonitor.jsx       # Theo dõi nhiệt độ, độ ẩm, ánh sáng
│   │   │   │   ├── FeedingControl.jsx           # Điều khiển hệ thống cho ăn tự động
│   │   │   │   ├── AlertPanel.jsx               # Hiển thị cảnh báo & sự cố
│   │   │   │   └── Charts.jsx                   # Biểu đồ thống kê, xu hướng dữ liệu
│   │   │   │
│   │   │   ├── Farm/             # Quản lý trang trại
│   │   │   │   ├── FarmMap.jsx               # Bản đồ trực quan trang trại & chuồng trại
│   │   │   │   └── CageViewer.jsx           # Xem chi tiết từng chuồng & thiết bị
│   │   │   │
│   │   │   ├── Records/          # Quản lý hồ sơ & dữ liệu
│   │   │   │   ├── FlockManagement.jsx      # Quản lý đàn gà (số lượng, độ tuổi, giống)
│   │   │   │   ├── HealthRecords.jsx        # Hồ sơ sức khỏe, tiêm phòng, bệnh
│   │   │   │   └── ProductionLog.jsx        # Ghi nhận sản xuất (trứng, cân nặng, v.v.)
│   │   │   │
│   │   │   └── Common/           # Thành phần dùng chung
│   │   │       ├── Navbar.jsx              # Thanh điều hướng
│   │   │       └── AlertNotification.jsx   # Thông báo & cảnh báo pop-up
│   │   │
│   │   ├── pages/                # Các trang chính ứng dụng
│   │   │   ├── Dashboard.jsx     # Trang tổng quan (hiển thị trạng thái trang trại)
│   │   │   ├── Farm.jsx          # Trang quản lý trang trại
│   │   │   ├── Records.jsx       # Trang xem & quản lý hồ sơ
│   │   │   └── Settings.jsx      # Cài đặt hệ thống & tài khoản
│   │   │
│   │   ├── services/             # Các dịch vụ giao tiếp với backend
│   │   │   ├── api.js            # Gọi REST API (GET, POST, PUT, DELETE)
│   │   │   ├── websocket.js      # Kết nối WebSocket cho dữ liệu real-time
│   │   │   └── auth.js           # Quản lý xác thực & token
│   │   │
│   │   ├── store/                # State management (Redux/Zustand)
│   │   │                         # Quản lý trạng thái toàn cục ứng dụng
│   │   │
│   │   ├── App.jsx               # Component gốc ứng dụng
│   │   ├── index.css             # CSS toàn cục
│   │   └── main.jsx              # Entry point React
│   │
│   ├── index.html                # Tệp HTML chính
│   ├── vite.config.js            # Cấu hình build tool (Vite)
│   ├── package.json              # Dependencies & scripts NPM
│   ├── package-lock.json         # Lock version dependencies
│   ├── .gitignore                # Bỏ qua file khi push Git
│   ├── .eslintrc.json            # Cấu hình linting code
│   └── README.md                 # Hướng dẫn frontend
│
├── backend/                      # API Backend (Flask/FastAPI)
│   ├── app/
│   │   ├── __init__.py           # Khởi tạo Flask app
│   │   ├── main.py               # Entry point backend
│   │   ├── config.py             # Cấu hình (database, MQTT, email, v.v.)
│   │   │
│   │   ├── api/                  # Các routes API
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Đăng ký, đăng nhập, đổi mật khẩu
│   │   │   ├── environment.py    # Endpoints lấy dữ liệu sensor (T, H, CO2, v.v.)
│   │   │   ├── feeding.py        # Điều khiển cho ăn tự động (khởi động, dừng, chế độ)
│   │   │   ├── health.py         # API theo dõi sức khỏe đàn gà
│   │   │   ├── records.py        # CRUD hồ sơ farm (flock, vaccination, production)
│   │   │   └── analytics.py      # Phân tích dữ liệu (báo cáo, thống kê, dự báo)
│   │   │
│   │   ├── models/               # Database models (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # Model người dùng (email, pass, role)
│   │   │   ├── device.py         # Model thiết bị IoT (tên, type, location)
│   │   │   ├── sensor_reading.py # Model dữ liệu cảm biến (T, H, timestamp)
│   │   │   ├── alert.py          # Model cảnh báo (loại, mức độ, trạng thái)
│   │   │   ├── flock.py          # Model đàn gà (số lượng, giống, tuổi, chuồng)
│   │   │   ├── health_record.py  # Model hồ sơ sức khỏe (bệnh, tiêm phòng, tedavi)
│   │   │   └── feeding_log.py    # Model ghi nhận cho ăn (lượng, giờ, trạng thái)
│   │   │
│   │   ├── services/             # Logic nghiệp vụ (decoupled từ routes)
│   │   │   ├── __init__.py
│   │   │   ├── data_processor.py      # Xử lý, làm sạch & chuẩn hóa dữ liệu sensor
│   │   │   ├── alert_service.py       # Tạo cảnh báo khi vượt ngưỡng
│   │   │   ├── ai_service.py          # Gọi AI models (detection, prediction)
│   │   │   ├── device_service.py      # Gửi lệnh đến thiết bị IoT
│   │   │   ├── notification_service.py # Gửi email/SMS khi có sự cố
│   │   │   └── analytics_service.py   # Tính toán thống kê, báo cáo
│   │   │
│   │   ├── ai/                   # Module AI/ML
│   │   │   ├── __init__.py
│   │   │   ├── disease_detector.py    # Load & sử dụng YOLOv8 phát hiện bệnh gà
│   │   │   ├── anomaly_detector.py    # Phát hiện bất thường trong môi trường
│   │   │   ├── predictor.py           # Dự báo sức khỏe, năng suất
│   │   │   └── models/
│   │   │       ├── yolov8_chicken.pt  # Model YOLOv8 đã train phát hiện bệnh
│   │   │       └── anomaly_model.pkl  # Model Isolation Forest/Autoencoder
│   │   │
│   │   ├── iot/                  # Tích hợp IoT
│   │   │   ├── __init__.py
│   │   │   ├── mqtt_handler.py        # Kết nối MQTT broker & xử lý callback
│   │   │   ├── device_manager.py      # Quản lý vòng đời thiết bị (register, remove)
│   │   │   └── command_executor.py    # Gửi lệnh điều khiển đến thiết bị
│   │   │
│   │   ├── tasks/                # Background jobs (Celery)
│   │   │   ├── __init__.py
│   │   │   ├── sensor_tasks.py        # Xử lý sensor streams định kỳ
│   │   │   ├── ai_tasks.py            # Chạy AI models theo schedule
│   │   │   ├── alert_tasks.py         # Tạo cảnh báo định kỳ
│   │   │   └── maintenance_tasks.py   # Dọn dẹp, tổng hợp dữ liệu cũ
│   │   │
│   │   ├── utils/                # Hàm tiện ích
│   │   │   ├── __init__.py
│   │   │   ├── validators.py     # Kiểm tra dữ liệu input (email, số, v.v.)
│   │   │   ├── thresholds.py     # Các ngưỡng cảnh báo (T, H, CO2, v.v.)
│   │   │   └── helpers.py        # Hàm trợ giúp chung
│   │   │
│   │   └── websocket/            # WebSocket real-time
│   │       ├── __init__.py
│   │       ├── events.py         # Xử lý sự kiện WebSocket (connect, disconnect)
│   │       └── namespace.py      # Cấu hình namespace cho Socket.IO
│   │
│   ├── migrations/               # Database migrations (Alembic)
│   │                            # Quản lý phiên bản database schema
│   │
│   ├── requirements.txt          # Python dependencies (Flask, SQLAlchemy, v.v.)
│   ├── .env                      # Biến môi trường (MQTT_URL, DB_URL, v.v.)
│   └── run.sh                    # Script chạy backend
│
├── iot/                          # Firmware & code cho thiết bị nhúng
│   ├── chicken_farm_firmware/
│   │   ├── chicken_farm_firmware.ino   # Sketch chính Arduino/ESP32
│   │   ├── config.h                   # Cấu hình WiFi SSID, mật khẩu, MQTT broker
│   │   ├── sensors.h                  # Khởi tạo & đọc cảm biến (DHT, CO2, v.v.)
│   │   ├── actuators.h                # Điều khiển relay, motor (quạt, đèn, bơm)
│   │   ├── mqtt_client.h              # Kết nối MQTT & publish/subscribe
│   │   └── display.h                  # Hiển thị trên LCD/OLED (T, H, cảnh báo)
│   │
│   └── sensor_calibration/       # Script calibration cảm biến
│       ├── calibrate_dht.py      # Calibrate cảm biến DHT22 (T, H)
│       └── calibrate_sensors.py  # Calibrate các cảm biến khác
│
├── ml/                           # Thư mục ML models & training
│   ├── training/
│   │   ├── disease_detection/
│   │   │   ├── train_yolov8.py       # Script train YOLOv8 phát hiện bệnh gà
│   │   │   ├── dataset.yaml          # Config dataset (train/val split, classes)
│   │   │   └── data/
│   │   │       ├── images/train      # Ảnh gà bệnh - tập train
│   │   │       ├── images/val        # Ảnh gà bệnh - tập validation
│   │   │       └── labels/           # Nhãn YOLO (bounding boxes)
│   │   │
│   │   ├── anomaly_detection/
│   │   │   ├── train_anomaly.py      # Train Isolation Forest/Autoencoder phát hiện bất thường
│   │   │   └── data/                 # Dữ liệu sensor bình thường & bất thường
│   │   │
│   │   └── production_prediction/
│   │       ├── train_prediction.py   # Train model dự báo năng suất (trứng/tuần, v.v.)
│   │       └── features.py           # Feature engineering từ dữ liệu sensor
│   │
│   ├── models/                   # Các model đã train
│   │   ├── yolov8_chicken.pt     # Trọng số YOLOv8 phát hiện bệnh
│   │   ├── anomaly_model.pkl     # Trọng số Isolation Forest/Autoencoder
│   │   └── production_model.pkl  # Trọng số dự báo sản xuất
│   │
│   └── evaluation/               # Đánh giá & validating models
│       ├── metrics.py            # Tính accuracy, precision, recall, F1
│       └── validation_report.md  # Báo cáo hiệu năng model
│
├── docker/                       # Docker containers
│   ├── Dockerfile.backend        # Container chạy Flask backend
│   ├── Dockerfile.frontend       # Container chạy React app
│   ├── Dockerfile.nginx          # Container Nginx reverse proxy
│   └── docker-compose.yml        # Orchestrate các container
│
├── docs/                         # Tài liệu dự án
│   ├── API_DOCUMENTATION.md      # Chi tiết các endpoint API
│   ├── INSTALLATION.md           # Hướng dẫn cài đặt toàn hệ thống
│   ├── IOT_SETUP.md              # Hướng dẫn setup firmware & thiết bị
│   ├── HUSBANDRY_REFERENCE.md    # Tham số chuẩn chăm sóc gà (T, H, tuổi, v.v.)
│   └── ARCHITECTURE.md           # Kiến trúc hệ thống tổng thể
│
├── tests/                        # Kiểm thử
│   ├── unit/                     # Unit tests
│   │   ├── test_services.py      # Test services (data processor, alert, v.v.)
│   │   └── test_models.py        # Test database models
│   │
│   ├── integration/              # Integration tests
│   │   └── test_api.py           # Test các API endpoints
│   │
│   └── e2e/                      # End-to-end tests
│       └── test_workflow.py      # Test workflow hoàn chỉnh (sensor → API → UI)
│
├── scripts/                      # Utility scripts
│   ├── setup_db.py               # Tạo database & tables
│   ├── seed_data.py              # Thêm dữ liệu mẫu
│   ├── train_models.sh           # Chạy training ML models
│   └── deploy.sh                 # Deployment script toàn hệ thống
│
├── .github/
│   └── workflows/                # CI/CD automation
│       ├── ci.yml                # Chạy tests tự động khi push code
│       └── deploy.yml            # Deploy tự động đến server
│
├── .gitignore                    # Bỏ qua file (node_modules, .env, v.v.)
├── .env.example                  # Template biến môi trường
└── README.md                     # Hướng dẫn chung dự án
```