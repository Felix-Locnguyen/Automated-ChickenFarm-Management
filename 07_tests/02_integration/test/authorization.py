"""Test phân quyền multi-user (B7) — A không thấy data của B; admin thấy tất."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# bootstrap như camera/pairing — chạy trực tiếp file vẫn import được
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "02_backend"))

from app.database import SessionLocal
from app.main import app
from app.models.alert import Alert
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _login(client, email):
    client.post("/api/auth/register",
                json={"email": email, "password": "matkhau123", "full_name": email})
    r = client.post("/api/auth/login", json={"email": email, "password": "matkhau123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def user_a(client):
    return _login(client, "a@gmail.com")


@pytest.fixture(scope="module")
def user_b(client):
    return _login(client, "b@gmail.com")


@pytest.fixture(scope="module")
def admin(client):
    h = _login(client, "admin@gmail.com")
    db = SessionLocal()          # set role thẳng qua DB (API chưa có endpoint đổi role)
    db.query(User).filter(User.email == "admin@gmail.com").update({"role": "admin"})
    db.commit()
    db.close()
    return h


@pytest.fixture(scope="module")
def flock_a(client, user_a):
    r = client.post("/api/flocks", json={"name": "Chuồng A", "chicken_count": 10},
                    headers=user_a)
    assert r.status_code == 200
    return r.json()["id"]


def test_b_khong_thay_chuong_cua_a(client, user_a, user_b, flock_a):
    ids_b = [f["id"] for f in client.get("/api/flocks", headers=user_b).json()]
    assert flock_a not in ids_b                          # B không thấy đàn A
    ids_a = [f["id"] for f in client.get("/api/flocks", headers=user_a).json()]
    assert flock_a in ids_a                              # A vẫn thấy đàn mình


def test_b_khong_doc_sua_xoa_chuong_cua_a(client, user_b, flock_a):
    for method, url in [("GET", f"/api/flocks/{flock_a}"),
                        ("PUT", f"/api/flocks/{flock_a}"),
                        ("DELETE", f"/api/flocks/{flock_a}")]:
        body = {"name": "hack", "chicken_count": 1}
        r = client.request(method, url, headers=user_b, json=body)
        assert r.status_code == 404, f"{method} {url} phải 404 (che giấu)"


def test_admin_thay_tat_ca(client, admin, flock_a):
    ids = [f["id"] for f in client.get("/api/flocks", headers=admin).json()]
    assert flock_a in ids


def test_thiet_bi_da_ghep_bi_che_chong_b(client, user_a, user_b, flock_a):
    r = client.post("/api/devices",
                    json={"name": "Cam A", "type": "camera", "flock_id": flock_a},
                    headers=user_a)
    assert r.status_code == 200
    dev_id = r.json()["id"]
    ids_b = [d["id"] for d in client.get("/api/devices", headers=user_b).json()]
    assert dev_id not in ids_b                           # B không thấy thiết bị đã ghép của A
    # B không toggle được (404 — kiểm quyền TRƯỚC khi chạm MQTT)
    r = client.put(f"/api/devices/{dev_id}/toggle", headers=user_b)
    assert r.status_code == 404


def test_thiet_bi_vo_chu_ai_cung_thay(client, user_a, user_b):
    r = client.post("/api/devices", json={"name": "Cam moi", "type": "camera"},
                    headers=user_a)                      # flock_id=None → vô chủ
    assert r.status_code == 200
    dev_id = r.json()["id"]
    ids_b = [d["id"] for d in client.get("/api/devices", headers=user_b).json()]
    assert dev_id in ids_b                               # vô chủ → ai cũng thấy (để ghép QR)


def test_alert_loc_theo_chu(client, user_a, user_b, admin, flock_a):
    db = SessionLocal()
    a1 = Alert(type="test", message="alert của A", flock_id=flock_a)
    a2 = Alert(type="test", message="alert hệ thống", flock_id=None)   # như camera
    db.add_all([a1, a2])
    db.commit()
    ids_a = [x["id"] for x in client.get("/api/alerts", headers=user_a).json()]
    ids_b = [x["id"] for x in client.get("/api/alerts", headers=user_b).json()]
    ids_admin = [x["id"] for x in client.get("/api/alerts", headers=admin).json()]
    assert a1.id in ids_a and a1.id not in ids_b         # alert chuồng A → chỉ A thấy
    # alert chưa gắn flock (MVP 1 trang trại, sensor chưa có device) → MỌI user thấy
    assert a2.id in ids_a and a2.id in ids_b and a2.id in ids_admin
    # B không resolve được alert GẮN CHUỒNG của A (404 che giấu)
    r = client.put(f"/api/alerts/{a1.id}/resolve", headers=user_b)
    assert r.status_code == 404
    db.close()
