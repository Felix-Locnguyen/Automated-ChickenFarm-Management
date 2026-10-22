# -*- coding: utf-8 -*-
"""
GHI BÁO CÁO ĐÁNH GIÁ → evaluation/validation_report.md
(Tổng hợp số liệu + link toàn bộ figure đã vẽ).
"""
import time

from config import REPORT_CSV, REPORT_MD, p


def write_report(per_model, extras=None):
    """
    Ghi validation_report.md.
      per_model — {tên model: số liệu detection (tp/fp/fn/P/R/F1/mAP/iou_avg)}
      extras    — {models, train_rows, speed, complexity}
    """
    extras = extras or {}
    lines = [
        "# BÁO CÁO ĐÁNH GIÁ MÔ HÌNH — YOLO26 Nhận diện gà broiler",
        "",
        f"_Tạo tự động bởi `training/chicken_detection/pipeline.py` — "
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "## 1. Dữ liệu",
        "",
    ]
    if REPORT_CSV.exists():
        import pandas as pd
        df = pd.read_csv(REPORT_CSV)
        lines += [
            f"- Tổng số id: **{len(df)}** | hợp lệ: **{int(df['is_label_valid'].sum())}** | "
            f"ảnh khớp nhãn: **{int(df['is_label_matched'].sum())}**",
            "- Chi tiết từng mẫu: [`data_report.csv`](data_report.csv)",
            "- Biểu đồ GĐ1: ![bar](figures/fig01_bar_labels.png) | "
            "![hist](figures/fig02_hist_dims.png) | ![channels](figures/fig03_hist_channels.png) | "
            "![checks](figures/fig04_pie_bar_checks.png) | ![samples](figures/fig05_samples10.png)",
            "",
        ]

    # ── 2. Huấn luyện
    lines += ["## 2. Kết quả huấn luyện (results.csv)", ""]
    for name in extras.get("models", []):
        lines += [f"### {name}", "",
                  f"![loss](figures/fig06_loss_curves_{name}.png)", "",
                  f"![metrics](figures/fig07_metrics_curve_{name}.png)", ""]
        tr = extras.get("train_rows", {}).get(name)
        if tr:
            lines.append(f"- Epoch cuối: {tr}")
            lines.append("")

    # ── 3. Detection metrics
    lines += ["## 3. Detection Metrics (test set, benchmark thủ công)", ""]
    if per_model:
        lines += ["| Model | TP | FP | FN | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for name, m in per_model.items():
            lines.append(f"| {name} | {m['tp']} | {m['fp']} | {m['fn']} | "
                         f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | "
                         f"{m['map50']:.3f} | {m['map95']:.3f} |")
        lines.append("")
        for name, m in per_model.items():
            i = m["iou_avg"]
            lines += [f"**{name}**", "",
                      "| IoU | GIoU | DIoU | CIoU | SIoU |", "|---|---|---|---|---|",
                      f"| {i['IoU']:.3f} | {i['GIoU']:.3f} | {i['DIoU']:.3f} | "
                      f"{i['CIoU']:.3f} | {i['SIoU']:.3f} |", "",
                      f"![cm](figures/fig08_confusion_matrix_{name}.png)", "",
                      f"![iou](figures/fig09_iou_variants_{name}.png)", "",
                      f"![pr](figures/fig10_pr_curve_{name}.png)", ""]
    else:
        lines += ["_Chưa có kết quả — chạy `--stage eval` sau khi train.", ""]

    # ── 4. Speed
    lines += ["## 4. Speed & Latency", ""]
    for name, sp in extras.get("speed", {}).items():
        lines += [f"**{name}** — {sp['n']} ảnh (warmup 20): "
                  f"pre {sp['pre']:.2f} ms | infer {sp['inf']:.2f} ms | "
                  f"post {sp['post']:.2f} ms | **tổng {sp['total']:.2f} ms → {sp['fps']:.1f} FPS**",
                  "", f"![speed](figures/fig11_speed_{name}.png)", ""]

    # ── 5. Complexity
    lines += ["## 5. Complexity & Tài nguyên", "",
              "| Model | Params | GFLOPs | Weights (MB) | Peak RAM % | Peak VRAM MB |",
              "|---|---|---|---|---|---|"]
    for name, cx in extras.get("complexity", {}).items():
        lines.append(f"| {name} | {cx['params']:,} | {cx['flops_g']:.2f} | "
                     f"{cx['size_mb']:.1f} | {cx['peak_ram_pct']:.0f} | {cx['peak_vram_mb']:.0f} |")
    lines.append("")
    for name in extras.get("complexity", {}):
        lines += [f"![cx](figures/fig12_complexity_{name}.png)", ""]

    # ── 6. Ghi chú
    lines += ["## 6. Ghi chú", "",
              "- Dataset: `Chicken.v2-wideangle_yewon_v2` (Roboflow, CC BY 4.0) — nhãn gốc "
              "POLYGON, đã convert → bbox, chỉ mẫu hợp lệ đưa vào train.",
              "- Augmentation động (xám/đèn ấm/nhiễu) áp dụng theo xác suất lúc train, "
              "không ghi đè ảnh gốc.",
              "- YOLO26 (hệ v8+) không còn nhánh objectness riêng; loss = box + cls + l1.",
              "- AP tính theo all-point interpolation; mAP@0.5:0.95 trung bình IoU "
              "0.5→0.95 bước 0.05; detections lọc conf≥ngưỡng eval.",
              "- SIoU = IoU − (Λ + Δ + Ω)/2 (Tong et al., 2023).",
              "- Log tài nguyên: [`system_performance_log.csv`](system_performance_log.csv)",
              ""]

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    p(f"Đã ghi báo cáo: {REPORT_MD}")
