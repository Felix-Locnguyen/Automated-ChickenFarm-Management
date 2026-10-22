# -*- coding: utf-8 -*-
"""
GĐ1b — XỬ LÝ dữ liệu:
  - LỌC    : chỉ mẫu is_label_valid = 1 được đưa vào train
  - CHUYỂN : polygon → bbox 5 cột (qua module encoding)
  - Dựng lại thư mục train-ready chicken_v2_yolo/ + data.yaml
  ⚠ Dữ liệu GỐC (chicken_v2/) không bao giờ bị ghi đè.
"""
import shutil
from pathlib import Path

from config import CLASS_NAMES, DATA_YAML, SPLITS, YOLO_DIR, p
from encoding import parse_label_line, to_yolo_line


def write_data_yaml():
    """data.yaml mà ultralytics đọc (path / train / val / test / nc / names)."""
    DATA_YAML.write_text(
        f"path: {YOLO_DIR}\n"
        "train: ./train/images\nval: ./valid/images\ntest: ./test/images\n\n"
        f"nc: {len(CLASS_NAMES)}\n"
        f"names: {list(CLASS_NAMES.values())}\n"
    )


def build_yolo_tree(df):
    """
    Dựng lại chicken_v2_yolo/ từ các mẫu hợp lệ của df.
    Mỗi mẫu: copy ảnh + ghi nhãn đã convert sang bbox 5 cột. Trả về số mẫu.
    """
    # dựng lại từ đầu → idempotent, không sót file của lần chạy trước
    if YOLO_DIR.exists():
        shutil.rmtree(YOLO_DIR)
    for sp in SPLITS:
        (YOLO_DIR / sp / "images").mkdir(parents=True, exist_ok=True)
        (YOLO_DIR / sp / "labels").mkdir(parents=True, exist_ok=True)

    n = 0
    for _, row in df[df["is_label_valid"] == 1].iterrows():
        sp = row["id"].split("_")[0]                 # 'train_12' → 'train'
        src_img = Path(row["img_path"])
        src_lbl = Path(row["label_path"])

        out_lines = []
        for line in src_lbl.read_text().strip().splitlines():
            cls_id, vals, kind, err = parse_label_line(line)
            if not err:                              # (mẫu hợp lệ nên mọi dòng đều pass)
                out_lines.append(to_yolo_line(cls_id, vals, kind))

        dst_lbl = YOLO_DIR / sp / "labels" / f"{src_lbl.stem}.txt"
        dst_img = YOLO_DIR / sp / "images" / src_img.name
        dst_lbl.write_text("\n".join(out_lines) + "\n")
        shutil.copy2(src_img, dst_img)
        n += 1

    write_data_yaml()
    p(f"Đã copy {n} mẫu hợp lệ (bbox 5 cột) → {YOLO_DIR}")
    p(f"data.yaml: {DATA_YAML}")
    return n
