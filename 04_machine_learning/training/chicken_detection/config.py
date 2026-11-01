# -*- coding: utf-8 -*-
"""
CẤU HÌNH CHUNG — đường dẫn, hằng số, hàm in log.
Mọi module đều import từ đây (nguồn duy nhất — single source of truth).
"""
from pathlib import Path

# ── Đường dẫn (file này nằm ở .../training/chicken_detection/config.py) ──
ML_ROOT = Path(__file__).resolve().parents[2]        # = 04_machine_learning/
# DỮ LIỆU MỚI — Chicken Counting v18 (Roboflow, YOLO26 format) — đã giải nén
# thành dạng train-ready: 5288 ảnh 640×640, split train/valid/test = 3696/1098/494.
# ⚠ Nằm SẴN ở dạng YOLO → GĐ1 chỉ validate, KHÔNG convert lại
#   (build_yolo_tree tự bỏ qua khi RAW_DIR == YOLO_DIR để tránh xóa data).
RAW_DIR = ML_ROOT / "datasets" / "chicken_counting_v18_yolo"
YOLO_DIR = ML_ROOT / "datasets" / "chicken_counting_v18_yolo"
# Weight + báo cáo của model train trên data cũ được backup tại
# models/chicken_detection/backup_chicken_counting_v18/
EVAL_DIR = ML_ROOT / "evaluation"                    # báo cáo + biểu đồ + log
FIG_DIR = EVAL_DIR / "figures"
RUNS_DIR = ML_ROOT / "models" / "chicken_detection" / "runs"   # weight + results.csv (bạn đã dời sang models/)

DATA_YAML = YOLO_DIR / "data.yaml"                   # ultralytics đọc file này
REPORT_CSV = EVAL_DIR / "data_report.csv"            # báo cáo kiểm tra từng mẫu
PERF_CSV = EVAL_DIR / "system_performance_log.csv"   # log CPU/RAM/GPU/VRAM
REPORT_MD = EVAL_DIR / "validation_report.md"        # báo cáo đánh giá cuối

SPLITS = ("train", "valid", "test")
CLASS_NAMES = {0: "chicken"}                              # tên lớp (nc=1) — theo data.yaml gốc của Chicken Counting v18 (Roboflow)
AUG_PROBS = {"gray": 0.15, "warm": 0.25, "noise": 0.25}   # xác suất augmentation
INTERACTIVE_MODE = True                                   # True = hỏi [Y/n] trước khi train


def p(msg=""):
    """In log (flush ngay để thấy khi chạy nền)."""
    print(msg, flush=True)


def header(title):
    """In tiêu đề phần."""
    p()
    p("=" * 70)
    p(f"  {title}")
    p("=" * 70)


def ensure_dirs():
    """Tạo sẵn thư mục đầu ra."""
    for d in (EVAL_DIR, FIG_DIR, RUNS_DIR):
        d.mkdir(parents=True, exist_ok=True)
