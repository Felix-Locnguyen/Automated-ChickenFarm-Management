#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════
 PIPELINE YOLO26 — Nhận diện gà / chicken (4 giai đoạn)
 File : 04_machine_learning/training/chicken_detection/pipeline.py
 Nhóm thành các module nhỏ (cùng thư mục):

   config.py      — đường dẫn, hằng số, hàm log
   encoding.py    — MÃ HÓA: validate dòng label, polygon→bbox, YOLO↔pixel
   data_check.py  — KIỂM TRA (GĐ1a): quét dataset → data_report.csv
   data_process.py— XỬ LÝ  (GĐ1b): lọc mẫu, convert, dựng chicken_counting_v18_yolo/
   features.py    — TẠO ĐẶC TRƯNG (GĐ2): augmentation động Albumentations
   viz.py         — toàn bộ biểu đồ (GĐ1/GĐ2/GĐ4)
   training.py    — HUẤN LUYỆN (GĐ3): profiler tài nguyên, xác nhận [Y/n]
   evaluation.py  — ĐÁNH GIÁ (GĐ4): IoU-variants, TP/FP/FN, P/R/F1/AP/mAP,
                     speed, complexity
   report.py      — ghi validation_report.md
   pipeline.py    — ĐIỀU PHỐI (file này): argparse + gọi 4 giai đoạn

 Cách chạy (trong 04_machine_learning/training/chicken_detection/):
   python pipeline.py --stage validate   # GĐ1: kiểm tra + xử lý dữ liệu
   python pipeline.py --stage aug        # GĐ2: xem trước augmentation
   python pipeline.py --stage train      # GĐ3: huấn luyện (hỏi [Y/n])
   python pipeline.py --stage eval       # GĐ4: đánh giá + báo cáo
   python pipeline.py --stage all        # chạy cả 4 giai đoạn
═════════════════════════════════════════════════════════════════════════
"""
import argparse
import time

from config import DATA_YAML, RAW_DIR, ensure_dirs, header, p
from data_check import save_report, scan_dataset
from data_process import build_yolo_tree
from evaluation import stage4_eval
from training import stage3_train
import viz


# ── GĐ1 / GĐ2 (điều phối các module kiểm tra + xử lý + biểu đồ) ───────

def stage1():
    """Kiểm tra dữ liệu gốc → lọc + convert → báo cáo + biểu đồ."""
    header("GIAI ĐOẠN 1 — KIỂM TRA & XỬ LÝ DỮ LIỆU")
    assert RAW_DIR.exists(), f"Thiếu dữ liệu gốc: {RAW_DIR}"
    df = scan_dataset()           # data_check — quét, đánh cờ hợp lệ
    save_report(df)               # data_check — data_report.csv
    build_yolo_tree(df)           # data_process — convert polygon→bbox, copy mẫu tốt
    viz.data_charts(df)           # viz — 5 biểu đồ GĐ1 (gọi sau khi có yolo tree)
    header("GĐ1 HOÀN TẤT — xem evaluation/figures/")


def stage2():
    """Xem trước 3 phép augmentation trên 1 ảnh mẫu."""
    header("GIAI ĐOẠN 2 — XEM TRƯỚC AUGMENTATION")
    assert DATA_YAML.exists(), "Thiếu chicken_v2_yolo/data.yaml — chạy --stage validate trước"
    viz.aug_preview()
    header("GĐ2 HOÀN TẤT — xem evaluation/figures/fig13_aug_preview.png")


# ── argparse ──────────────────────────────────────────────────────────

def build_parser():
    ap = argparse.ArgumentParser(
        description="Pipeline YOLO26 — nhận diện gà / chicken (4 giai đoạn)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--stage", choices=["validate", "aug", "train", "eval", "all"],
                    default="all", help="giai đoạn cần chạy")
    ap.add_argument("--models", nargs="+", default=["yolo8n", "yolo8s"],
                    choices=["yolo8n", "yolo8s"],
                    help="model YOLO8 cần huấn luyện/đánh giá")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--lr0", type=float, default=0.001)
    ap.add_argument("--optimizer", default="SGD", choices=["SGD", "Adam", "AdamW", "auto"])
    ap.add_argument("--patience", type=int, default=20, help="early-stop chống overfit")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--conf", type=float, default=0.25, help="ngưỡng conf lúc eval")
    ap.add_argument("--speed-images", type=int, default=200, help="số ảnh benchmark (100–500)")
    ap.add_argument("--prof-interval", type=float, default=3.0, help="chu kỳ log CPU/GPU (giây)")
    ap.add_argument("--device", default=None, help="mặc định: tự detect (0=GPU, 'cpu')")
    ap.add_argument("--no-interactive", action="store_true",
                    help="bỏ qua bước xác nhận [Y/n] (INTERACTIVE_MODE=False)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.device is None:
        import torch
        args.device = 0 if torch.cuda.is_available() else "cpu"
    ensure_dirs()

    t0 = time.time()
    if args.stage in ("validate", "all"):
        stage1()
    if args.stage in ("aug", "all"):
        stage2()
    if args.stage in ("train", "all"):
        stage3_train(args)          # training.py
    if args.stage in ("eval", "all"):
        stage4_eval(args)           # evaluation.py
    p(f"\n⏱  Tổng thời gian: {(time.time() - t0) / 60:.1f} phút")


if __name__ == "__main__":
    main()
