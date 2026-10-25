#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giả lập ESP32-CAM — POST ảnh snapshot định kỳ vào backend, KHÔNG cần phần cứng.

Kịch bản xen kẽ để test cả 2 nhánh pipeline:
  1. Ảnh THẬT từ dataset  → model thấy gà  → backend LƯU (DB + ảnh + alert)
  2. Ảnh TRỐNG (tô màu)    → model không thấy gì → backend DISCARD (không lưu)

Chạy (mở 2 service trước — xem README yolo-service):
  .venv/bin/python 08_scripts/simulate_esp32cam.py --interval 10 --count 6

Args:
  --interval   giây giữa 2 lần chụp (mặc định 30 — như ESP32-CAM thật)
  --count      số lần chụp (0 = chạy mãi, Ctrl+C để dừng; mặc định 6)
  --backend    backend URL (mặc định http://localhost:8020)
"""
import argparse
import io
import random
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "04_machine_learning" / "datasets" / "chicken_v2_yolo"


def real_images() -> list[Path]:
    """Toàn bộ ảnh trong dataset train-ready (xoay vòng)."""
    files = sorted(DATASET.glob("*/images/*"))
    if not files:
        sys.exit(f"Thiếu ảnh dataset: {DATASET}/* /images — chạy --stage validate trước")
    return files


def blank_jpeg() -> bytes:
    """Ảnh trống (tô xám) — model không phát hiện gì → nhánh DISCARD."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (640, 480), (128, 128, 128)).save(buf, format="JPEG")
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description="Giả lập ESP32-CAM gửi snapshot")
    ap.add_argument("--interval", type=float, default=30, help="giây giữa 2 lần chụp")
    ap.add_argument("--count", type=int, default=6, help="số lần chụp (0 = mãi)")
    ap.add_argument("--backend", default="http://localhost:8020")
    args = ap.parse_args()

    imgs = real_images()
    url = f"{args.backend.rstrip('/')}/api/camera/snapshot"
    print(f"→ Gửi {url} mỗi {args.interval}s — dataset {len(imgs)} ảnh thật")
    print("  (Ctrl+C để dừng)\n")

    i = 0
    sent = saved = discarded = errors = 0
    try:
        while args.count == 0 or i < args.count:
            i += 1
            # xen kẽ: chẵn = ảnh thật (detected), lẻ = ảnh trống (discard)
            if i % 2 == 1:
                data, label = imgs[random.randrange(len(imgs))].read_bytes(), "ảnh thật"
            else:
                data, label = blank_jpeg(), "ảnh trống"
            try:
                r = httpx.post(url, files={"file": ("cam.jpg", data, "image/jpeg")},
                               timeout=20.0)
                r.raise_for_status()
                body = r.json()
                sent += 1
                status = body.get("status")
                if status == "detected":
                    saved += 1
                    print(f"[{i:02d}] {label:11s} → DETECTED  {body['count']:>2} cá thể, "
                          f"lưu #{body['detection_id']}, img={body.get('img_url')}")
                elif status == "normal":
                    discarded += 1
                    print(f"[{i:02d}] {label:11s} → normal    không phát hiện → DISCARD ✔")
                else:
                    errors += 1
                    print(f"[{i:02d}] {label:11s} → LỖI      {body}")
            except Exception as e:
                errors += 1
                print(f"[{i:02d}] {label:11s} → THẤT BẠI {e}\n"
                      "       (backend/yolo-service chưa mở? xem README yolo-service)")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass

    print(f"\nTổng: gửi {sent} | lưu {saved} | discard {discarded} | lỗi {errors}")


if __name__ == "__main__":
    main()
