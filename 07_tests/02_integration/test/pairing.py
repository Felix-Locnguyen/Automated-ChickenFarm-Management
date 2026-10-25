"""Test ghép thiết bị qua pairing code (B6 — Phase 4).

Vòng đời: đăng ký+đăng nhập → tạo đàn → tạo thiết bị CHƯA ghép → GET qr → POST pair
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Chạy trực tiếp file (python pairing.py / nút Run trong editor) thì KHÔNG qua
# pytest → conftest.py không được nạp → tự nạp đường dẫn 02_backend cho chắc.
# parents[3] = gốc repo (test → 02_integration → 07_tests → repo)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "02_backend"))

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
def device(client, auth_headers):
    """Thiết bị MỚI — chưa ghép chuồng (flock_id=None), ghép bằng QR ở test pair."""
    r = client.post("/api/devices",
                    json={"name": "Camera QR", "type": "camera"},
                    headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["pairing_code"]          # tạo thiết bị phải có code ngay
    assert body["flock_id"] is None      # chưa ghép → QR mới có việc để làm
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


def test_pair_lai_bi_tu_choi(client, auth_headers, flock_id, device):
    # Lần 1: thiết bị chưa ghép + user có đàn → ghép được
    r1 = client.post("/api/devices/pair",
                     json={"pairing_code": device["pairing_code"]},
                     headers=auth_headers)
    assert r1.status_code == 200
    # Lần 2: đã ghép rồi → 400 (đúng lý do: flock_id đã có)
    r2 = client.post("/api/devices/pair",
                     json={"pairing_code": device["pairing_code"]},
                     headers=auth_headers)
    assert r2.status_code == 400


def test_pair_sai_code_tra_404(client, auth_headers):
    r = client.post("/api/devices/pair",
                    json={"pairing_code": "ZZZZ99"},
                    headers=auth_headers)
    assert r.status_code == 404
