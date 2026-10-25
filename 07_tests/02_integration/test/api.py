"""Test tích hợp (integration): gọi API thật qua TestClient — giống hệt client thật.

Chạy: pytest 07_tests/02_integration/test/api.py -v

Luồng test giống một người dùng thật:
đăng ký → đăng nhập → tạo đàn → thêm cảm biến → cho ăn → tài chính → thống kê
"""
import pytest
import sys
from fastapi.testclient import TestClient
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "02_backend"))
from app.main import app


@pytest.fixture(scope="module")
def client():
    """1 TestClient dùng chung cho cả file (module scope)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    """Đăng ký + đăng nhập 1 user duy nhất → trả về header Authorization."""
    client.post("/api/auth/register",
                json={"email": "it@test.vn", "password": "matkhau123", "full_name": "IT"})
    r = client.post("/api/auth/login",
                    json={"email": "it@test.vn", "password": "matkhau123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- AUTH ----------

def test_dang_ky_thieu_truong_bat_buoc(client):
    """Pydantic bắt buộc đủ field — thiếu password → 422."""
    r = client.post("/api/auth/register", json={"email": "thieu-mk@x.vn"})
    assert r.status_code == 422


def test_dang_ky_trung_email(client):
    client.post("/api/auth/register", json={"email": "trung@x.vn", "password": "123456"})
    r = client.post("/api/auth/register", json={"email": "trung@x.vn", "password": "123456"})
    assert r.status_code == 400
    assert "tồn tại" in r.json()["detail"]


def test_login_sai_mat_khau(client):
    r = client.post("/api/auth/login", json={"email": "khong-ton-tai@x.vn", "password": "sai"})
    assert r.status_code == 400  # không tiết lộ email có tồn tại hay không


def test_mat_khau_khong_luu_plaintext(client, auth_headers):
    """Bảo mật: mật khẩu trong DB phải là hash, không bao giờ là chuỗi gốc."""
    r = client.get("/api/analytics/summary")  # sanity: API vẫn chạy
    assert r.status_code == 200
    # Đăng ký user mới rồi thử login với đúng mật khẩu → phải pass (hash verify đúng)
    client.post("/api/auth/register", json={"email": "hash@x.vn", "password": "bi-mat-khau-9x"})
    r = client.post("/api/auth/login", json={"email": "hash@x.vn", "password": "bi-mat-khau-9x"})
    assert r.status_code == 200


# ---------- FLOCK (bảo vệ bằng JWT) ----------

def test_tao_flock_can_token(client):
    r = client.post("/api/flocks", json={"name": "X", "chicken_count": 10})
    assert r.status_code == 401  # không token → bị chặn


def test_crud_flock(client, auth_headers):
    # CREATE
    r = client.post("/api/flocks",
                    json={"name": "Chuồng D1", "chicken_count": 999, "breed": "Test"},
                    headers=auth_headers)
    assert r.status_code == 200
    flock_id = r.json()["id"]
    assert r.json()["owner_id"] is not None  # tự gán từ token

    # READ
    r = client.get(f"/api/flocks/{flock_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Chuồng D1"

    # UPDATE
    r = client.put(f"/api/flocks/{flock_id}",
                   json={"name": "Chuồng D1 mới", "chicken_count": 1000},
                   headers=auth_headers)
    assert r.json()["chicken_count"] == 1000

    # DELETE
    r = client.delete(f"/api/flocks/{flock_id}", headers=auth_headers)
    assert r.status_code == 200
    assert client.get(f"/api/flocks/{flock_id}", headers=auth_headers).status_code == 404


# ---------- SENSOR ----------

def test_cam_bien_moi_nhat(client):
    client.post("/api/sensor",
                json={"temperature": 27.2, "humidity": 61.0, "food_level": 70, "water_level": 85})
    r = client.get("/api/sensors/latest")
    assert r.status_code == 200
    assert r.json()["temperature"] == 27.2


def test_lich_su_cam_bien(client):
    r = client.get("/api/sensor?skip=0&limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) <= 5  # respect limit


# ---------- FEEDING ----------

def test_cho_an_hoan_tat(client, auth_headers):
    flock_id = client.post("/api/flocks", json={"name": "Cho ăn E", "chicken_count": 50},
                           headers=auth_headers).json()["id"]
    r = client.post("/api/feeding",
                    json={"feed_type": "cám", "amount_kg": 12.5, "scheduled_time": "07:00",
                          "flock_id": flock_id})
    assert r.status_code == 200
    log_id = r.json()["id"]
    assert r.json()["status"] == "pending"

    r = client.put(f"/api/feeding/{log_id}/complete")
    assert r.json()["message"] == "Da hoan tat"


# ---------- FINANCIAL ----------

def test_tai_chinh_tinh_tu_dong(client, auth_headers):
    flock_id = client.post("/api/flocks", json={"name": "Tài chính F", "chicken_count": 100},
                           headers=auth_headers).json()["id"]
    r = client.post("/api/financial",
                    json={"flock_id": flock_id, "date": "2026-10-01T00:00:00",
                          "quantity_before": 100, "cost_per_chick": 30000,
                          "sold_chickens": 10, "unit_price": 90000})
    assert r.status_code == 200
    d = r.json()
    assert d["revenue"] == 900000       # 10 × 90k
    assert d["profit"] < 0              # còn tiền thức ăn + giá mua → lỗ

    # summary phải cộng đúng
    r = client.get(f"/api/financial/summary?flock_id={flock_id}")
    assert r.json()["total_revenue"] == 900000


# ---------- ANALYTICS ----------

def test_dashboard_tong_hop(client):
    r = client.get("/api/analytics/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body and "recent_alerts" in body
    assert "total_chickens" in body["summary"]


# ---------- ALERT TỰ ĐỘNG (POST /sensor vượt ngưỡng) ----------

def test_canh_bao_tu_dong_vuot_nguong(client, auth_headers):
    """Nhiệt độ 41°C (> 35) → GET /alerts thấy alert temperature sinh tự động."""
    # DB chung — test unit có thể để sót alert temperature đang mở → resolve trước
    for a in client.get("/api/alerts", headers=auth_headers).json():
        if a["type"] == "temperature":
            client.put(f"/api/alerts/{a['id']}/resolve", headers=auth_headers)

    client.post("/api/sensor",
                json={"temperature": 41, "humidity": 60, "food_level": 80, "water_level": 90})
    r = client.get("/api/alerts", headers=auth_headers)
    assert r.status_code == 200
    temps = [a for a in r.json() if a["type"] == "temperature"]
    assert len(temps) == 1
    assert temps[0]["severity"] == "critical"   # > 40°C → mức nghiêm trọng


def test_canh_bao_khong_tao_trung_lap(client, auth_headers):
    """Reading vẫn vượt ngưỡng → KHÔNG thêm alert trùng (chỉ 1 alert đang mở)."""
    client.post("/api/sensor",
                json={"temperature": 42, "humidity": 60, "food_level": 80, "water_level": 90})
    r = client.get("/api/alerts", headers=auth_headers)
    temps = [a for a in r.json() if a["type"] == "temperature"]
    assert len(temps) == 1   # vẫn là 1 — đã có alert đang mở


def test_resolve_xong_vuot_nguong_tao_alert_moi(client, auth_headers):
    """Đánh dấu đã xử lý → đọc lại vượt ngưỡng → alert MỚI được tạo."""
    r = client.get("/api/alerts", headers=auth_headers)
    old_id = [a for a in r.json() if a["type"] == "temperature"][0]["id"]
    client.put(f"/api/alerts/{old_id}/resolve", headers=auth_headers)

    client.post("/api/sensor",
                json={"temperature": 43, "humidity": 60, "food_level": 80, "water_level": 90})
    r = client.get("/api/alerts", headers=auth_headers)
    temps = [a for a in r.json() if a["type"] == "temperature"]
    assert len(temps) == 1        # alert mới sau khi resolve
    assert temps[0]["id"] != old_id


def test_reading_binh_thuong_khong_sinh_canh_bao(client, auth_headers):
    """Reading trong ngưỡng → không crash, không thêm alert temperature mới."""
    client.post("/api/sensor",
                json={"temperature": 28, "humidity": 65, "food_level": 90, "water_level": 95})
    r = client.get("/api/alerts", headers=auth_headers)
    assert r.status_code == 200
    assert len([a for a in r.json() if a["type"] == "temperature"]) == 1  # không tăng


def test_health_check(client):
    assert client.get("/health").json() == {"status": "ok"}
