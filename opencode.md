# Opencode - Automated Chicken Farm Management

## Tổng quan dự án
- **Tên:** Hệ thống Quản lý Trang trại Gà Thông minh
- **Stack:** React 19 + Vite 8 (Frontend) | FastAPI + PostgreSQL (Backend)
- **Theme:** Warm brown (#654321, #d4a574), Vietnamese UI
- **Rule:** Hỏi user trước khi thêm feature mới (threshold ≤ 50%)

---

## Cấu trúc dự án

```
AutomatedChickenFarmManagemen-v2/
├── 01_frontend/
│   ├── static.html              ← HTML prototype gốc (2761 dòng)
│   ├── index.html
│   ├── package.json
│   └── 02_src/
│       ├── main.jsx
│       ├── App.jsx              ← Main app (state + handlers)
│       ├── App.css              ← Tất cả CSS (~1360 dòng)
│       ├── index.css
│       ├── 01_assets/
│       ├── 02_components/
│       │   ├── 02.1_Dashboard/
│       │   │   ├── EnvironmentMonitor.jsx  ✅
│       │   │   ├── FeedingControl.jsx      ✅
│       │   │   ├── AlertPanel.jsx          ✅
│       │   │   ├── Charts.jsx              ⬜ placeholder
│       │   │   └── DevicesList.jsx         ✅
│       │   ├── 02.2_Farm/
│       │   │   ├── CoopDetailView.jsx      ✅ (camera-grid 2 cameras)
│       │   │   ├── CoopsList.jsx           ✅
│       │   │   ├── CoopsSearchList.jsx     ✅
│       │   │   ├── CageViewer.jsx          ✅
│       │   │   └── FarmMap.jsx             ⬜ placeholder
│       │   ├── 02.3_Financial/             ← MỚI
│       │   │   ├── FinancialTab.jsx        ✅ tab container
│       │   │   ├── IncomeForm.jsx          ✅ form nhập thu
│       │   │   ├── ExpenseForm.jsx         ✅ form nhập chi
│       │   │   ├── RecentRecords.jsx       ✅ 5 bản ghi gần nhất
│       │   │   ├── HistoryModal.jsx        ✅ modal lịch sử
│       │   │   └── RecordDetailModal.jsx   ✅ modal chi tiết
│       │   ├── 02.4_FinanceManagement/     ← MỚI
│       │   │   ├── FinanceManagementTab.jsx ✅ tab container
│       │   │   ├── FilterBar.jsx           ✅ filter 7/30/365 ngày
│       │   │   ├── FinanceChart.jsx        ✅ biểu đồ cột CSS
│       │   │   └── FinanceSummary.jsx      ✅ tổng thu/chi/LN
│       │   ├── 02.4_Common/
│       │   │   ├── Navbar.jsx              ✅ 5 nút: 🏠🐔💵📊⚙️
│       │   │   └── AlertNotification.jsx   ✅ toast
│       │   ├── 02.5_Devices/
│       │   │   └── DevicesList.jsx         ✅
│       │   └── 02.6_Common/
│       │       └── DeleteCoopModal.jsx     ✅ modal xóa chuồng
│       ├── 03_pages/
│       │   ├── Dashboard.jsx               ✅
│       │   ├── Farm.jsx                    ✅
│       │   ├── Devices.jsx                 ✅
│       │   ├── Records.jsx                 ⬜ placeholder
│       │   └── Settings.jsx                ⬜ placeholder
│       ├── 04_services/
│       └── 05_store/
├── 02_backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry
│   │   ├── config.py            ← DB config (port 5050)
│   │   ├── database.py          ← SQLAlchemy engine
│   │   ├── models/              ← 8 models
│   │   │   ├── user.py
│   │   │   ├── flock.py
│   │   │   ├── device.py
│   │   │   ├── alert.py
│   │   │   ├── sensor/reading.py
│   │   │   ├── feeding/log.py
│   │   │   ├── health/record.py
│   │   │   └── financial/record.py  ← MỚI
│   │   ├── api/
│   │   │   ├── schemas.py       ← Pydantic schemas
│   │   │   ├── financial.py     ← 6 routes CRUD + summary
│   │   │   ├── auth.py
│   │   │   ├── environment.py
│   │   │   ├── feeding.py
│   │   │   ├── records.py
│   │   │   ├── health.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── data_processor.py
│   │   │   ├── alert.py
│   │   │   ├── ai.py
│   │   │   ├── device.py
│   │   │   ├── notification.py
│   │   │   └── analytics.py
│   │   └── iot/
│   │       ├── mqtt_handler.py
│   │       ├── device_manager.py
│   │       └── command_executor.py
│   ├── requirements.txt
│   ├── .env
│   └── alembic/
│       ├── ini
│       └── migrations/env.py
└── opencode.md
```

---

## Các công việc đã làm

### Phase 1: Khởi tạo & Fix bugs (26/08)
- Fix 13+ bugs (syntax, typos, relationships, imports, folder naming)
- Tạo `requirements.txt`, `.env`, `alembic.ini`, `migrations/env.py`
- Verified all Python imports thành công

### Phase 2: Backend features
- **IoT:** MQTT handler, device manager, command executor
- **AI:** Predictor, disease detector, anomaly detector (placeholders)
- **Tasks:** Sensor, AI, alert, maintenance tasks
- **WebSocket:** Events, namespace
- **Services:** data_processor, alert, ai, device, notification, analytics
- **API Routes:** auth, environment, feeding, records, health, analytics

### Phase 3: Frontend React
- Fix `index.css`, import case sensitivity, `index.html`
- Extract components into numbered folders
- Compose pages (Dashboard, Farm, Devices)
- Refactor App.jsx: 381 → 220 lines

### Phase 4: Financial features (static.html)
- **Tab Tài chính (+):** Income/expense forms, recent records, history modal, detail modal
- **Tab Quản lí TC (📊):** Filter bar, bar chart CSS, summary boxes
- **Modal xóa chuồng:** Mã xác nhận 4 chữ số
- **Camera grid:** 2 cameras xếp dọc (1×2)

### Phase 5: Financial features (React)
- Tạo 12 components mới (02.3_Financial + 02.4_FinanceManagement)
- Cập nhật Navbar: 5 nút 🏠🐔💵📊⚙️
- Cập nhật App.jsx: +2 tab, +state, +handlers
- Copy ~500 dòng CSS

---

## Navbar hiện tại

```
[🏠 Trang chủ] [🐔 Quản lý gà] [💵 Tài chính] [📊 Quản lí TC] [⚙️ Thiết bị]
```

---

## Backend database

- **PostgreSQL:** password=1, port=5050, database=chicken_farm
- **Tables:** users, flocks, devices, alerts, sensor_readings, feeding_logs, health_records, financial_records
- **API:** http://localhost:8000/docs (Swagger)

---

## Tỷ lệ hoàn thành

| Module | static.html | React |
|--------|-------------|-------|
| Dashboard | 100% | 100% |
| Quản lý gà | 100% | 100% |
| Tài chính (nhập) | 100% | 100% |
| Quản lí TC (biểu đồ) | 100% | 100% |
| Thiết bị | 100% | 100% |
| Camera grid 2×1 | 100% | 100% |
| Records/Hồ sơ | - | ⬜ placeholder |
| Settings | - | ⬜ placeholder |
| Charts | - | ⬜ placeholder |

---

## Next steps (sau khi upload Git)

1. **Records tab:** FlockManagement, HealthRecords, ProductionLog
2. **Charts:** Biểu đồ thống kê Dashboard
3. **Settings:** Cài đặt hệ thống
4. **Connect API:** Liên kết React với Backend
5. **Auth:** Đăng nhập/đăng ký
