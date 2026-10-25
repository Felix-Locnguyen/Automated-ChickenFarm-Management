import pytest
from fastapi.testclient import TestClient

from app.main import app




@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    client.post("/api/auth/register",
                json={"email": "pair@test.vn", "password": "matkhau123", "full_name": "Pair"})
    r = client.post("/api/auth/login",
                    json={"email": "pair@test.vn", "password": "matkhau123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def flock_id(client, auth_headers):
    r = client.post("/api/flocks",
                    json={"name": "Chuồng QR", "chicken_count": 100},
                    headers=auth_headers)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture()
def device(client, auth_headers, flock_id):
    r = client.post("/api/devices",
                    json={"name": "Camera QR", "type": "camera", "flock_id": flock_id},
                    headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["pairing_code"]          # tạo thiết bị phải có code ngay
    return body


def test_lay_qr_co_code_va_anh(client, auth_headers, device):
    r = client.get(f"/api/devices/{device['id']}/qr", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["pairing_code"] == device["pairing_code"]     # code giữ nguyên, không đổi
    assert body["pair_url"].endswith(f"?token={body['pairing_code']}")
    assert body["qr_image"].startswith("data:image/png;base64,")


def test_pair_thanh_cong(client, auth_headers, flock_id, device):
    r = client.post("/api/devices/pair",
                    json={"pairing_code": device["pairing_code"]},
                    headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["flock_id"] == flock_id                  # ghép vào đàn của user này
    assert r.json()["paired_at"] is not None


def test_pair_lai_bi_tu_choi(client, auth_headers, device):
    r = client.post("/api/devices/pair",
                    json={"pairing_code": device["pairing_code"]},
                    headers=auth_headers)
    assert r.status_code == 400                              # đã ghép rồi → 400


def test_pair_sai_code_tra_404(client, auth_headers):
    r = client.post("/api/devices/pair",
                    json={"pairing_code": "ZZZZ99"},
                    headers=auth_headers)
    assert r.status_code == 404