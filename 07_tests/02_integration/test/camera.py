"""Test tích hợp router camera — MOCK yolo-service (không cần chạy service thật).

Chạy: pytest 07_tests/02_integration/test/camera.py -v

3 kịch bản theo nguyên tắc "chỉ lưu ảnh có phát hiện":
  1. 0 phát hiện      → discard (không lưu)
  2. có phát hiện     → lưu DB + trả detection_id
  3. yolo-service chết → 502
"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Bootstrap giống pairing.py: chạy trực tiếp file không qua conftest
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "02_backend"))

from app.main import app
from app.services import camera_service


def _jpg() -> bytes:
    """1 ảnh JPEG nhỏ giả lập snapshot."""
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 90, 60)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _post(client):
    return client.post("/api/camera/snapshot",
                       files={"file": ("snapshot.jpg", _jpg(), "image/jpeg")})


def test_anh_binh_thuong_bi_discard(client, monkeypatch):
    monkeypatch.setattr(camera_service, "detect_image",
                        lambda data: {"count": 0, "detections": []})
    r = _post(client)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "normal"
    assert body["saved"] is False          # ★ không lưu gì


def test_co_phat_hien_luu_vao_db(client, monkeypatch):
    det = [{"bbox": [1.0, 2.0, 30.0, 40.0], "conf": 0.91, "cls": 0, "cls_name": "broiler"}]
    monkeypatch.setattr(camera_service, "detect_image",
                        lambda data: {"count": 1, "detections": det})
    r = _post(client)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "detected"
    assert body["saved"] is True
    assert body["detection_id"] >= 1

    # /camera/latest phải thấy lần phát hiện này
    latest = client.get("/api/camera/latest").json()["detection"]
    assert latest is not None
    assert latest["id"] == body["detection_id"]
    assert latest["detections"] == det


def test_yolo_service_chet_tra_502(client, monkeypatch):
    monkeypatch.setattr(camera_service, "detect_image", lambda data: None)
    r = _post(client)
    assert r.status_code == 502
