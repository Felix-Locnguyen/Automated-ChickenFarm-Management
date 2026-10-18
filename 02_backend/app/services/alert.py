"""Tự động tạo cảnh báo khi cảm biến gửi readings vượt ngưỡng.

Gọi từ POST /sensor sau khi lưu reading:
    check_reading_and_alert(db, reading)

Ngưỡng mặc định hard-code (Phase 2: chuyển sang bảng thresholds cho từng chuồng).
"""
from sqlalchemy.orm import Session

from ..models.alert import Alert
from ..models.device import Device
from ..models.sensor.reading import SensorReading

# Ngưỡng mặc định — tạm hard-code, Phase 2 sẽ đọc từ bảng thresholds theo chuồng
DEFAULT_THRESHOLDS = {
    "temp_max": 35.0,    # trên này → quạt/đèn cần can thiệp
    "temp_min": 20.0,
    "hum_max": 80.0,
    "hum_min": 40.0,
    "food_min": 30.0,    # dưới 30% → sắp hết thức ăn
    "water_min": 30.0,
}


def _violations(reading: SensorReading) -> list[dict]:
    """So sánh reading với ngưỡng → trả về danh sách vi phạm (rỗng nếu ổn).

    Mỗi phần tử: { type, severity, message } — khớp field của model Alert.
    """
    t = DEFAULT_THRESHOLDS
    v = []

    if reading.temperature > t["temp_max"]:
        sev = "critical" if reading.temperature > 40 else "warning"
        v.append({"type": "temperature", "severity": sev,
                  "message": f"Nhiệt độ cao: {reading.temperature}°C (ngưỡng {t['temp_max']}°C)"})
    if reading.temperature < t["temp_min"]:
        v.append({"type": "temperature", "severity": "warning",
                  "message": f"Nhiệt độ thấp: {reading.temperature}°C (ngưỡng {t['temp_min']}°C)"})
    if reading.humidity > t["hum_max"]:
        v.append({"type": "humidity", "severity": "warning",
                  "message": f"Độ ẩm cao: {reading.humidity}% (ngưỡng {t['hum_max']}%)"})
    if reading.humidity < t["hum_min"]:
        v.append({"type": "humidity", "severity": "warning",
                  "message": f"Độ ẩm thấp: {reading.humidity}% (ngưỡng {t['hum_min']}%)"})
    if reading.food_level < t["food_min"]:
        v.append({"type": "feeding", "severity": "warning",
                  "message": f"Thức ăn sắp hết: {reading.food_level}% (ngưỡng {t['food_min']}%)"})
    if reading.water_level < t["water_min"]:
        v.append({"type": "water", "severity": "warning",
                  "message": f"Nước sắp hết: {reading.water_level}% (ngưỡng {t['water_min']}%)"})
    return v


def _has_open_alert(db: Session, alert_type: str, device_id: int | None) -> bool:
    """Chống lặp: đã có alert CÙNG type + CÙNG device CHƯA resolved chưa?

    Nếu cứ mỗi reading vượt ngưỡng lại tạo alert mới → web ngập alert trùng nhau.
    """
    query = db.query(Alert).filter(
        Alert.type == alert_type,
        Alert.is_resolved == False,  # noqa: E712 — SQLAlchemy so sánh cột, không dùng `is`
    )
    if device_id:
        query = query.filter(Alert.device_id == device_id)
    else:
        query = query.filter(Alert.device_id.is_(None))
    return query.first() is not None


def check_reading_and_alert(db: Session, reading: SensorReading) -> list[Alert]:
    """Xét reading vừa lưu → tạo Alert cho mỗi loại vi phạm chưa có alert đang mở.

    Trả về danh sách alert MỚI tạo (rỗng nếu reading trong ngưỡng).
    """
    violations = _violations(reading)
    if not violations:
        return []

    # Tra cứu chuồng sở hữu cảm biến (device.flock_id) để gắn vào alert
    flock_id = None
    if reading.device_id:
        device = db.query(Device).filter(Device.id == reading.device_id).first()
        flock_id = device.flock_id if device else None

    created = []
    for v in violations:
        if _has_open_alert(db, v["type"], reading.device_id):
            continue  # đã có alert đang mở cho loại này → không tạo trùng
        alert = Alert(
            type=v["type"],
            severity=v["severity"],
            message=v["message"],
            flock_id=flock_id,
            device_id=reading.device_id,
        )
        db.add(alert)
        created.append(alert)

    if created:
        db.commit()
        for a in created:
            db.refresh(a)
    return created
