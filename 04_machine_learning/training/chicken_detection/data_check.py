# -*- coding: utf-8 -*-
"""
GĐ1a — KIỂM TRA dữ liệu gốc (không đụng gì đến file):
  Quét 3 split, mỗi id 1 dòng báo cáo với các cờ:
    is_file_exist    — ảnh có tồn tại?
    is_label_matched — nhãn có khớp tên file ảnh?
    is_label_valid   — nhãn hợp lệ? (không rỗng, class đúng, tọa độ ∈ [0,1])
  → data_report.csv
"""
import cv2

from config import CLASS_NAMES, RAW_DIR, REPORT_CSV, SPLITS, p
from encoding import parse_label_line


def _check_label(img_path, lbl_path, row):
    """
    Validate file nhãn, điền cờ vào row (is_label_valid/label_kind/target_name).
    Trả về '' nếu hợp lệ, ngược lại trả lý do (để ghi vào cột note).
    """
    if lbl_path is None:
        return "thiếu file nhãn"
    if img_path is None:
        return "có nhãn nhưng KHÔNG có ảnh (mồ côi)"
    lines = lbl_path.read_text().strip().splitlines()
    if not lines:
        return "file nhãn rỗng (0 dòng)"

    kinds, classes = set(), set()
    for line in lines:
        cls_id, _vals, kind, err = parse_label_line(line)
        kinds.add(kind)
        if err:
            return f"dòng không hợp lệ: {err}"
        classes.add(cls_id)
    row["is_label_valid"] = 1
    row["label_kind"] = "+".join(sorted(k for k in kinds if k != "invalid"))
    row["target_name"] = ",".join(CLASS_NAMES[c] for c in sorted(classes))
    return ""


def scan_dataset():
    """Quét toàn bộ dataset GỐC → pandas.DataFrame (1 dòng = 1 id)."""
    import pandas as pd

    rows = []
    for sp in SPLITS:
        img_dir = RAW_DIR / sp / "images"
        lbl_dir = RAW_DIR / sp / "labels"
        stems_img = {f.stem: f for f in sorted(img_dir.glob("*"))} if img_dir.exists() else {}
        stems_lbl = {f.stem: f for f in sorted(lbl_dir.glob("*.txt"))} if lbl_dir.exists() else {}
        all_stems = sorted(set(stems_img) | set(stems_lbl))
        p(f"[{sp}] ảnh: {len(stems_img)} | nhãn: {len(stems_lbl)} | tổng id: {len(all_stems)}")

        for i, stem in enumerate(all_stems):
            img_path, lbl_path = stems_img.get(stem), stems_lbl.get(stem)
            row = {
                "id": f"{sp}_{i}",
                "target_name": "",
                "img_width": "", "img_height": "", "img_channels": "",
                "label_path": str(lbl_path or ""),
                "img_path": str(img_path or ""),
                "is_file_exist": int(img_path is not None),
                "is_label_matched": int(img_path is not None and lbl_path is not None),
                "is_label_valid": 0,
                "label_kind": "",
                "note": "",
            }

            # ảnh: kích thước + số kênh (1 = xám, 3 = RGB, 4 = RGBA)
            if img_path is not None:
                im = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
                if im is None:
                    row["note"] = "không đọc được ảnh"
                else:
                    h, w = im.shape[:2]
                    row.update(img_width=w, img_height=h,
                               img_channels=1 if im.ndim == 2 else im.shape[2])

            # nhãn: lỗi label (nếu có) ghi đè note
            err = _check_label(img_path, lbl_path, row)
            if err:
                row["note"] = err
            rows.append(row)

    return pd.DataFrame(rows)


def save_report(df):
    """Ghi data_report.csv + in tóm tắt."""
    df.to_csv(REPORT_CSV, index=False)
    n_ok = int((df["is_label_valid"] == 1).sum())
    p(f"\nTổng id: {len(df)} | hợp lệ: {n_ok} | loại: {len(df) - n_ok}")
    p(f"Báo cáo: {REPORT_CSV}")
