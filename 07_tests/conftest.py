"""Conftest chung cho mọi test — chạy 1 lần trước khi test bắt đầu.

- Thêm thư mục 02_backend vào sys.path để `import app...` hoạt động
- Ép dùng SQLite cho test (KHÔNG đụng vào Postgres thật)
"""
import os
import sys
from pathlib import Path

import pytest

# sys.path: cho phép `from app.main import app` dù pytest chạy từ gốc repo
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02_backend"))

# PHẢI đặt TRƯỚC khi import app.main — vì app.config đọc DATABASE_URL lúc import.
# override=False (mặc định): nếu biến đã có trong env thì giữ nguyên — an toàn.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_farm.db")


@pytest.fixture(scope="session", autouse=True)
def clean_db():
    """XÓA file DB cũ trước khi bắt đầu session test.

    SQLite relative path (./test_farm.db) lưu theo thư mục chạy pytest —
    nếu file cũ còn tồn tại, dữ liệu các lần chạy trước sẽ "rò rỉ" làm test fail.
    """
    db_file = Path("test_farm.db")
    if db_file.exists():
        db_file.unlink()
    yield
