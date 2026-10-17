"""Test đơn vị (unit) cho các model ORM — kiểm tra bảng + relationship hoạt động.

Chạy: pytest 07_tests/01_unit/test/models.py -v
"""
import pytest
from sqlalchemy import inspect

from app.database import Base, SessionLocal, engine
from app.models import Alert, Device, Flock, SensorReading, User


@pytest.fixture()
def db():
    """Tạo bảng + 1 session sạch cho mỗi test, dọn dẹp sau khi xong.

    drop_all trước: mỗi test bắt đầu với DB trống hoàn toàn —
    tránh dữ liệu test trước "rò rỉ" sang test sau.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_tat_ca_bang_duoc_tao(db):
    """Sau create_all, Postgres/SQLite phải có đủ 8 bảng của dự án."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected = {"users", "flocks", "devices", "alerts",
                "sensor_readings", "feeding_logs", "health_records", "financial_records"}
    assert expected.issubset(tables), f"Thieu bang: {expected - tables}"


def test_tao_user_va_flock(db):
    """User 1 — N Flock: tạo 1 user + 2 đàn gà, kiểm tra quan hệ."""
    user = User(email="test@farm.vn", hashed_password="x", full_name="Tester")
    db.add(user)
    db.flush()

    db.add(Flock(name="A1", chicken_count=100, owner_id=user.id))
    db.add(Flock(name="B2", chicken_count=200, owner_id=user.id))
    db.commit()

    assert db.query(Flock).count() == 2
    # relationship: user.flocks tự nạp danh sách đàn gà
    assert len(user.flocks) == 2
    assert user.flocks[0].owner.email == "test@farm.vn"  # chiều ngược lại cũng hoạt động


def test_flock_device_alert(db):
    """Flock 1 — N Device; Alert nối cả Flock lẫn Device."""
    user = User(email="a@b.c", hashed_password="x")
    db.add(user)
    db.flush()
    flock = Flock(name="C3", chicken_count=50, owner_id=user.id)
    db.add(flock)
    db.flush()

    device = Device(name="Quạt C3", type="fan", status="online", flock_id=flock.id)
    db.add(device)
    db.flush()

    db.add(Alert(type="temperature", severity="warning",
                 message="Nóng", flock_id=flock.id, device_id=device.id))
    db.commit()

    assert flock.devices[0].type == "fan"
    assert flock.alerts[0].severity == "warning"
    assert device.alerts[0].message == "Nóng"


def test_trang_thai_mac_dinh(db):
    """Các default của model: role=farmer, device status=offline, alert severity=warning."""
    user = User(email="d@e.f", hashed_password="x")
    db.add(user)
    db.commit()
    assert user.role == "farmer"  # default trong model

    device = Device(name="cam", type="camera")
    db.add(device)
    db.commit()
    assert device.status == "offline"
    assert device.is_active is False


def test_sensor_reading_khong_can_flock(db):
    """SensorReading chỉ cần device_id — nhưng device_id=None vẫn OK (nullable)."""
    reading = SensorReading(temperature=28.0, humidity=65.0, food_level=80, water_level=90)
    db.add(reading)
    db.commit()
    assert reading.id is not None
    assert reading.created_at is not None  # server_default=func.now() tự điền
