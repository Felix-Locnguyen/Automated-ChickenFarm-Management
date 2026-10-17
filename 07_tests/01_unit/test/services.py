"""Test nghiệp vụ: AnalyticsService + hàm tính tài chính.

Chạy: pytest 07_tests/01_unit/test/services.py -v
"""
from datetime import datetime, timedelta

import pytest

from app.api.financial import calculate_fields
from app.database import Base, SessionLocal, engine
from app.models import Alert, Flock, SensorReading, User
from app.services.analytics_service import AnalyticsService


@pytest.fixture()
def db():
    """Mỗi test 1 DB sạch (drop + create lại) — không lộ dữ liệu giữa các test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_calculate_fields_loi_nhuan_du_tinh_dung():
    """Bài toán: 4500 gà × 32k mua vào, bán 400 × 95k, gà chết 15, feed 18tr, khác 2.5tr."""
    from app.api.schemas import FinancialRecordCreate

    data = FinancialRecordCreate(
        flock_id=1, date=datetime(2026, 10, 1),
        quantity_before=4500, cost_per_chick=32000,
        dead_chickens=15, sold_chickens=400, unit_price=95000,
        feed_cost=18_000_000, other_cost=2_500_000,
    )
    calc = calculate_fields(data)

    expected_revenue = 400 * 95000            # 38,000,000
    expected_depreciation = 15 * 32000        # 480,000
    expected_chick_cost = 4500 * 32000        # 144,000,000
    expected_total = expected_chick_cost + 18_000_000 + 2_500_000 + expected_depreciation
    expected_profit = expected_revenue - expected_total

    assert calc["revenue"] == expected_revenue
    assert calc["depreciation_cost"] == expected_depreciation
    assert calc["total_cost"] == expected_total
    assert calc["profit"] == expected_profit


def test_get_farm_summary(db):
    """Summary phải tổng hợp đúng tổng đàn + cảnh báo đang mở + reading mới nhất."""
    user = User(email="s@b.c", hashed_password="x")
    db.add(user)
    db.flush()
    db.add(Flock(name="A1", chicken_count=1000, owner_id=user.id))
    db.add(Flock(name="B2", chicken_count=2500, owner_id=user.id))
    db.add(Alert(type="temperature", severity="warning", message="Nóng", is_resolved=False))
    db.add(Alert(type="humidity", severity="warning", message="Ẩm", is_resolved=True))  # đã xử lý → KHÔNG đếm
    db.add(SensorReading(temperature=29.5, humidity=70.0, food_level=55, water_level=88))
    db.commit()

    summary = AnalyticsService(db).get_farm_summary()

    assert summary["total_chickens"] == 3500     # 1000 + 2500
    assert summary["active_alerts"] == 1         # chỉ alert chưa resolved
    assert summary["temperature"] == 29.5        # reading mới nhất
    assert summary["humidity"] == 70.0


def test_get_sensor_history_loc_theo_gio(db):
    """Chỉ trả readings trong N giờ gần nhất — bản ghi cũ phải bị loại."""
    db.add(SensorReading(temperature=30.0, humidity=60.0, food_level=1, water_level=1))
    db.commit()
    # giả lập bản ghi cũ bằng cách backdate (SQLite: cập nhật thẳng created_at)
    old = db.query(SensorReading).first()
    old.created_at = datetime.utcnow() - timedelta(hours=48)
    db.add(SensorReading(temperature=28.0, humidity=65.0, food_level=2, water_level=2))
    db.commit()

    rows = AnalyticsService(db).get_sensor_history(hours=24)

    assert len(rows) == 1                        # bản ghi 48h trước bị loại
    assert rows[0]["temperature"] == 28.0
    assert isinstance(rows[0]["created_at"], str)  # đã serialize ISO string


def test_get_alert_stats_nhom_theo_severity(db):
    db.add(Alert(type="temperature", severity="warning", message="a"))
    db.add(Alert(type="humidity", severity="warning", message="b"))
    db.add(Alert(type="feeding", severity="critical", message="c"))
    db.commit()

    stats = AnalyticsService(db).get_alert_stats(days=7)

    assert stats == {"warning": 2, "critical": 1}
