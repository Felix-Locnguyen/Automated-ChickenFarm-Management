"""Seed dữ liệu mẫu cho trang trại gà.

Cách chạy (trong thư mục 02_backend):
    ../.venv/bin/python ../08_scripts/seed/data.py

Script này tạo:
- 1 tài khoản admin (email: admin@farm.vn, mật khẩu: admin123)
- 3 đàn gà (A1 đẻ, B2 thịt, C3 gà con)
- Thiết bị + cảm biến + lịch cho ăn + hồ sơ sức khỏe + phiếu tài chính
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Cho phép import package "app" dù chạy file từ thư mục khác
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02_backend"))

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Alert,
    Device,
    FeedingLog,
    FinancialRecord,
    Flock,
    HealthRecord,
    SensorReading,
    User,
)

NOW = datetime.utcnow()


def seed():
    Base.metadata.create_all(bind=engine)  # tạo bảng nếu chưa có
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("DB da co du lieu — khong seed lai. (Xoa DB neu muon seed moi)")
            return

        # 1. Tài khoản admin
        admin = User(
            email="admin@farm.vn",
            hashed_password=hash_password("admin123"),
            full_name="Quản lý trại",
            role="admin",
        )
        db.add(admin)
        db.flush()  # flush: cho SQLAlchemy INSERT ngay để lấy admin.id (chưa commit)

        # 2. 3 đàn gà
        flocks_data = [
            {"name": "Chuồng Gà Đẻ A1", "chicken_count": 4200, "breed": "Lơ-đành", "age_weeks": 28, "coop_number": 1},
            {"name": "Chuồng Gà Thịt B2", "chicken_count": 5050, "breed": "Cobb 500", "age_weeks": 8, "coop_number": 2},
            {"name": "Chuồng Gà Con C3", "chicken_count": 3200, "breed": "Ross 308", "age_weeks": 3, "coop_number": 3},
        ]
        flocks = []
        for data in flocks_data:
            flock = Flock(**data, owner_id=admin.id)
            db.add(flock)
            flocks.append(flock)
        db.flush()

        # 3. Thiết bị cho mỗi chuồng (fan, light, feeder, camera)
        device_types = [("fan", "Quạt thông gió"), ("light", "Đèn sưởi"),
                        ("feeder", "Máy cho ăn"), ("camera", "Camera")]
        for flock in flocks:
            for dtype, dname in device_types:
                db.add(Device(
                    name=f"{dname} - {flock.name}",
                    type=dtype,
                    status="online" if dtype != "camera" else "warning",
                    is_active=(dtype in ("fan", "camera")),
                    flock_id=flock.id,
                ))
        db.flush()

        # 4. 10 bản ghi cảm biến gần nhất (giả lập cảm biến chuồng A1)
        device_sensor = db.query(Device).filter_by(type="fan", flock_id=flocks[0].id).first()
        for i in range(10, 0, -1):
            db.add(SensorReading(
                temperature=round(27.5 + (i % 3) * 0.8, 1),
                humidity=round(62 + (i % 4) * 2.5, 1),
                food_level=round(85 - i * 1.5, 1),
                water_level=90.0,
                device_id=device_sensor.id,
            ))
        # bản ghi cho 2 chuồng còn lại (device_id=None vì cảm biến chưa gán)
        db.add(SensorReading(temperature=30.2, humidity=71.0, food_level=45.0, water_level=80.0))
        db.add(SensorReading(temperature=29.0, humidity=68.5, food_level=92.0, water_level=95.0))

        # 5. 2 cảnh báo đang mở
        db.add(Alert(type="temperature", severity="warning",
                     message="Nhiệt độ chuồng B2 vượt ngưỡng (30.5°C)",
                     flock_id=flocks[1].id, is_resolved=False))
        db.add(Alert(type="humidity", severity="critical",
                     message="Độ ẩm chuồng B2 quá cao (78%) — nguy cơ bệnh hô hấp",
                     flock_id=flocks[1].id, is_resolved=False))

        # 6. Lịch cho ăn
        db.add(FeedingLog(feed_type="Ngô + cám", amount_kg=25.5, scheduled_time="06:30",
                          status="completed", flock_id=flocks[0].id))
        db.add(FeedingLog(feed_type="Cám viên", amount_kg=40.0, scheduled_time="17:30",
                          status="pending", flock_id=flocks[1].id))

        # 7. Hồ sơ sức khỏe
        db.add(HealthRecord(record_type="Tiêm phòng Newcastle",
                            description="Mũi 1 cho đàn A1", veterinarian="BS. Nguyễn Văn A",
                            flock_id=flocks[0].id))
        db.add(HealthRecord(record_type="Khám tổng quát",
                            description="Kiểm tra hô hấp đàn C3", veterinarian="BS. Trần Thị B",
                            flock_id=flocks[2].id))

        # 8. Phiếu tài chính (hệ thống tự tính profit — xem calculate_fields)
        db.add(FinancialRecord(
            flock_id=flocks[0].id, date=NOW - timedelta(days=10),
            quantity_before=4500, cost_per_chick=32000, dead_chickens=15,
            sold_chickens=400, unit_price=95000, feed_cost=18_000_000,
            other_cost=2_500_000, note="Bán lô 400 gà đẻ hết đẻ",
            depreciation_cost=15 * 32000, revenue=400 * 95000,
            total_cost=4500 * 32000 + 18_000_000 + 2_500_000 + 15 * 32000,
            profit=400 * 95000 - (4500 * 32000 + 18_000_000 + 2_500_000 + 15 * 32000),
        ))

        db.commit()
        print("=== SEED THANH CONG ===")
        print("Login: admin@farm.vn / admin123")
        print(f"3 đàn gà, 12 thiết bị, 12 readings, 2 alerts, 2 feeding, 2 health, 1 financial")
    except Exception:
        db.rollback()  # có lỗi → hoàn tác toàn bộ, DB không bị nửa vời
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
