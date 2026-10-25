#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo bucket MinIO (phương án Python — dự phòng cho job `minio-init` trong compose).

Yêu cầu: `pip install minio`  (hỏi trước khi cài!)

Chạy (khi MinIO đã up ở localhost:9000):
  .venv/bin/python 08_scripts/minio_init.py
"""
from minio import Minio

ENDPOINT = "localhost:9000"
ACCESS = "farmminio"
SECRET = "farmminio123"
BUCKET = "disease-images"


def main():
    client = Minio(ENDPOINT, access_key=ACCESS, secret_key=SECRET, secure=False)

    if client.bucket_exists(BUCKET):
        print(f"Bucket '{BUCKET}' đã tồn tại — không làm gì.")
    else:
        client.make_bucket(BUCKET)
        print(f"✓ Đã tạo bucket '{BUCKET}'")

    # Liệt kê bucket để xác nhận
    print("Danh sách bucket:", [b.name for b in client.list_buckets()])


if __name__ == "__main__":
    main()
