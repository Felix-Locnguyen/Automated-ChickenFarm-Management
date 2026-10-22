# -*- coding: utf-8 -*-
"""
BIỂU ĐỒ cho pipeline YOLO26 — mọi figure đều có TITLE + LEGEND + NHÃN TRỤC.
  PHẦN A — dữ liệu (GĐ1/GĐ2): bar, histogram, pie, 10 ảnh mẫu, xem trước aug
  PHẦN B — mô hình  (GĐ4)    : loss/metrics, Confusion Matrix, PR, IoU,
                               speed, complexity
"""
import cv2
import numpy as np

import matplotlib
matplotlib.use("Agg")                       # vẽ headless, không cần màn hình
import matplotlib.pyplot as plt

from config import CLASS_NAMES, FIG_DIR, RUNS_DIR, YOLO_DIR, p
from encoding import yolo_to_xyxy
from features import PhotometricAug


def find_col(df, *keys):
    """Tìm cột trong results.csv theo từ khóa (không cần biết tên chính xác)."""
    for k in keys:
        for col in df.columns:
            if k in col:
                return col
    return None


def _save(fig, name, dpi=110):
    """Lưu figure vào evaluation/figures/ rồi đóng."""
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=dpi)
    plt.close(fig)
    p(f"  ✓ figures/{name}")


# ══════════════════ PHẦN A — BIỂU ĐỒ DỮ LIỆU (GĐ1/GĐ2) ══════════════════

def data_charts(df):
    """5 biểu đồ GĐ1 (gọi sau khi đã dựng yolo tree — vì fig05 cần ảnh)."""
    _bar_labels(df)
    _hist_dims(df)
    _hist_channels(df)
    _checks_pie_bar(df)
    _samples_10(seed=42)


def _bar_labels(df):
    """Bar: số ẢNH chứa mỗi nhãn (chỉ mẫu hợp lệ)."""
    ok = df[df["is_label_valid"] == 1]
    counts = {name: 0 for name in CLASS_NAMES.values()}
    for names in ok["target_name"]:
        for nm in str(names).split(","):
            if nm in counts:
                counts[nm] += 1
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(list(counts.keys()), list(counts.values()), color="#4C9F70")
    ax.bar_label(bars, fontsize=11)
    ax.set_title("Số lượng ảnh theo từng nhãn (mẫu hợp lệ)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Tên nhãn (class)")
    ax.set_ylabel("Số ảnh")
    ax.legend(["Số ảnh"], loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "fig01_bar_labels.png")


def _hist_dims(df):
    """Histogram: phân bố chiều rộng / chiều cao ảnh."""
    ok = df[df["img_width"] != ""].copy()
    w, h = ok["img_width"].astype(int), ok["img_height"].astype(int)
    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.linspace(0, max(w.max(), h.max()), 25)
    ax.hist(w, bins=bins, alpha=0.6, label=f"Chiều rộng (TB={w.mean():.0f}px)", color="#3B82F6")
    ax.hist(h, bins=bins, alpha=0.6, label=f"Chiều cao (TB={h.mean():.0f}px)", color="#F59E0B")
    ax.axvline(w.mean(), color="#3B82F6", ls="--", lw=1.5)
    ax.axvline(h.mean(), color="#F59E0B", ls="--", lw=1.5)
    ax.set_title("Phân bố kích thước ảnh (Rộng × Cao)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số pixel (px)")
    ax.set_ylabel("Số lượng ảnh (tần suất)")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    _save(fig, "fig02_hist_dims.png")


def _hist_channels(df):
    """Bar: phân bố số kênh màu (1=xám, 3=RGB, 4=RGBA)."""
    ok = df[df["img_channels"] != ""]
    vc = ok["img_channels"].astype(int).value_counts().sort_index()
    labels = {1: "1 (xám)", 3: "3 (RGB)", 4: "4 (RGBA)"}
    names = [labels.get(v, str(v)) for v in vc.index]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(names, vc.values, color="#8B5CF6")
    ax.bar_label(bars, fontsize=11)
    ax.set_title("Phân bố số kênh màu của ảnh", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số kênh")
    ax.set_ylabel("Số lượng ảnh")
    ax.legend(["Số ảnh"], loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "fig03_hist_channels.png")


def _checks_pie_bar(df):
    """Pie: tỷ lệ khớp ảnh↔nhãn. Bar: tồn tại ảnh / khớp / hợp lệ."""
    n = len(df)
    matched = int(df["is_label_matched"].sum())
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    axes[0].pie([matched, n - matched], labels=["Khớp (ảnh+nhãn)", "Không khớp"],
                autopct="%1.1f%%", startangle=90, colors=["#4C9F70", "#E05D5D"])
    axes[0].set_title("Tỷ lệ khớp tên file ảnh ↔ nhãn", fontsize=12, fontweight="bold")
    axes[0].legend(loc="lower left")
    vals = [int(df["is_file_exist"].sum()), matched, int(df["is_label_valid"].sum())]
    bars = axes[1].bar(["Ảnh tồn tại", "Nhãn khớp", "Nhãn hợp lệ"], vals,
                       color=["#3B82F6", "#4C9F70", "#F59E0B"])
    axes[1].bar_label(bars, fontsize=11)
    axes[1].set_title("Kết quả kiểm tra tồn tại / hợp lệ", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Tiêu chí")
    axes[1].set_ylabel("Số mẫu")
    axes[1].set_ylim(0, n * 1.15)
    axes[1].legend(["Số mẫu đạt"], loc="upper right")
    axes[1].grid(axis="y", alpha=0.3)
    _save(fig, "fig04_pie_bar_checks.png")


def _samples_10(seed=42):
    """10 ảnh ngẫu nhiên (từ yolo tree) + bbox quy về pixel + tên lớp."""
    files = sorted((YOLO_DIR / "train" / "images").glob("*")) + \
            sorted((YOLO_DIR / "test" / "images").glob("*"))
    rng = np.random.default_rng(seed)
    picks = [files[i] for i in rng.permutation(len(files))[:10]]
    fig, axes = plt.subplots(2, 5, figsize=(20, 9))
    for ax, f in zip(axes.flat, picks):
        img = cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB)
        H, W = img.shape[:2]
        lbl = f.parent.parent / "labels" / f"{f.stem}.txt"
        for line in lbl.read_text().strip().splitlines():
            v = line.split()
            x1, y1, x2, y2 = (int(x) for x in yolo_to_xyxy(list(map(float, v[1:5])), W, H))
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 220, 60), 2)
            cv2.putText(img, CLASS_NAMES.get(int(v[0]), "?"), (x1, max(y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 40, 40), 2)
        ax.imshow(img)
        ax.set_title(f.stem[:26], fontsize=9)
        ax.axis("off")
    fig.suptitle("10 ảnh mẫu ngẫu nhiên + bounding box (tọa độ đã quy đổi về pixel)",
                 fontsize=15, fontweight="bold")
    _save(fig, "fig05_samples10.png", dpi=100)


def aug_preview():
    """Xem trước 3 phép augmentation trên 1 ảnh (stage 'aug')."""
    src = sorted((YOLO_DIR / "train" / "images").glob("*"))
    assert src, "Chưa có dữ liệu train-ready — chạy --stage validate trước"
    img = cv2.imread(str(src[0]))
    aug = PhotometricAug()
    panels = [("Ảnh gốc", img),
              (f"Xám (p={aug.p_gray})", aug.apply(img, "gray")),
              (f"Ánh đèn ấm (p={aug.p_warm})", aug.apply(img, "warm")),
              (f"Nhiễu Gaussian (p={aug.p_noise})", aug.apply(img, "noise"))]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
    for ax, (title, im) in zip(axes, panels):
        ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("px")
        ax.set_ylabel("px")
    fig.suptitle("Augmentation động (áp dụng theo xác suất lúc train — không ghi đè đĩa)",
                 fontsize=13, fontweight="bold")
    _save(fig, "fig13_aug_preview.png")


# ══════════════════ PHẦN B — BIỂU ĐỒ MÔ HÌNH (GĐ4) ══════════════════

def training_curves(name):
    """
    Đọc results.csv của run `name` → vẽ (1) Loss train/val qua epoch,
    (2) Precision/Recall/mAP qua epoch. Trả về df (None nếu chưa train).
    """
    import pandas as pd
    csv_path = RUNS_DIR / name / "results.csv"
    if not csv_path.exists():
        p(f"[bỏ qua] thiếu {csv_path}")
        return None
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    ecol = find_col(df, "epoch")
    epochs = df[ecol] if ecol else np.arange(1, len(df) + 1)

    # YOLO26 có l1_loss thay dfl_loss, không có obj_loss → tìm theo từ khóa
    panels = [("box", ("box_loss",)),
              ("cls/obj", ("cls_loss", "obj_loss")),
              ("dfl/l1", ("dfl_loss", "l1_loss"))]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, (title, keys) in zip(axes, panels):
        drawn = False
        for k in keys:
            tr, va = find_col(df, f"train/{k}"), find_col(df, f"val/{k}")
            if tr:
                ax.plot(epochs, df[tr], lw=2, label=f"train {k}", color="#3B82F6")
                drawn = True
            if va:
                ax.plot(epochs, df[va], lw=2, ls="--", label=f"val {k}", color="#F59E0B")
                drawn = True
        if not drawn:
            ax.text(0.5, 0.5, f"không có cột {keys[0]}", ha="center", transform=ax.transAxes)
        ax.set_title(f"{title.upper()} Loss", fontsize=12, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.legend()
        ax.grid(alpha=0.3)
    fig.suptitle(f"Diễn tiến Loss qua các Epoch — {name}", fontsize=14, fontweight="bold")
    _save(fig, f"fig06_loss_curves_{name}.png")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for key, color, label in [("precision", "#3B82F6", "Precision"),
                              ("recall", "#4C9F70", "Recall"),
                              ("mAP50", "#F59E0B", "mAP@0.5"),
                              ("mAP50-95", "#E05D5D", "mAP@0.5:0.95")]:
        col = find_col(df, f"metrics/{key}(B)", f"metrics/{key}")
        if col:
            ax.plot(epochs, df[col], lw=2, color=color, label=label)
    ax.set_title(f"Precision / Recall / mAP qua các Epoch — {name}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Giá trị (0–1)")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    _save(fig, f"fig07_metrics_curve_{name}.png")
    return df


def confusion_chart(cm, name, conf):
    """Heatmap ma trận nhầm lẫn (hàng = GT, cột = Predicted, có background)."""
    labels = [CLASS_NAMES[i] for i in range(len(CLASS_NAMES))] + ["background"]
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=30, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            v = cm[i, j]
            ax.text(j, i, str(v), ha="center", va="center",
                    color="white" if v > cm.max() * 0.6 else "black", fontweight="bold")
    ax.set_title(f"Confusion Matrix — {name} (test set, conf={conf})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Dự đoán (Predicted)")
    ax.set_ylabel("Thực tế (Ground Truth)")
    fig.colorbar(im, ax=ax, label="Số mẫu")
    _save(fig, f"fig08_confusion_matrix_{name}.png")


def pr_chart(rec, prec, i_best, f1_best, conf_best, name):
    """Đường cong Precision–Recall (điểm F1 tốt nhất được đánh dấu)."""
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.plot(rec, prec, lw=2.2, color="#3B82F6", label="PR curve")
    ax.scatter([rec[i_best]], [prec[i_best]], c="red", zorder=5,
               label=f"F1 tốt nhất={f1_best:.3f} @conf≈{conf_best:.2f}")
    ax.set_title(f"Precision–Recall — {name} (IoU=0.5)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    _save(fig, f"fig10_pr_curve_{name}.png")


def iou_chart(iou_avg, name):
    """Bar: IoU trung bình 5 biến thể (trên các cặp match @0.5)."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    keys = list(iou_avg.keys())
    bars = ax.bar(keys, [iou_avg[k] for k in keys],
                  color=["#3B82F6", "#4C9F70", "#F59E0B", "#8B5CF6", "#E05D5D"])
    ax.bar_label(bars, fmt="%.3f", fontsize=10)
    ax.set_title(f"IoU trung bình theo 5 biến thể — {name}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Biến thể IoU")
    ax.set_ylabel("Giá trị trung bình")
    ax.set_ylim(min(0, min(iou_avg.values()) - 0.1), 1.05)
    ax.legend(["mean (matched pairs)"], loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    _save(fig, f"fig09_iou_variants_{name}.png")


def speed_chart(sp, name):
    """Bar: thời gian pre/infer/post/total (ms) + FPS trên tiêu đề."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    labels = ["Pre-process", "Inference", "Post/NMS", "Tổng latency"]
    vals = [sp["pre"], sp["inf"], sp["post"], sp["total"]]
    bars = ax.bar(labels, vals, color=["#3B82F6", "#E05D5D", "#F59E0B", "#4C9F70"])
    ax.bar_label(bars, fmt="%.2f ms", fontsize=10)
    ax.set_title(f"Speed & Latency — {name} (FPS≈{sp['fps']:.1f})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Giai đoạn")
    ax.set_ylabel("Thời gian (ms)")
    ax.legend([f"TB {sp['n']} ảnh"], loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    _save(fig, f"fig11_speed_{name}.png")


def complexity_chart(cx, name):
    """4 panel: Parameters (M) | GFLOPs | Weight size (MB) | Peak RAM/VRAM."""
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))

    def bar0(ax, val, label, color, unit):
        b = ax.bar([label], [val], color=color)
        ax.bar_label(b, fmt=f"%.2f {unit}", fontsize=10)
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_ylabel(unit)
        ax.grid(axis="y", alpha=0.3)

    bar0(axes[0], cx["params"] / 1e6, "Parameters", "#3B82F6", "M")
    bar0(axes[1], cx["flops_g"], "FLOPs", "#8B5CF6", "G")
    bar0(axes[2], cx["size_mb"], "Weight size", "#F59E0B", "MB")
    if not np.isnan(cx["peak_vram_mb"]):
        b = axes[3].bar(["Peak RAM %", "Peak VRAM"], [cx["peak_ram_pct"], cx["peak_vram_mb"]],
                        color=["#4C9F70", "#E05D5D"])
        axes[3].bar_label(b, fontsize=10)
        axes[3].set_title("Peak tài nguyên", fontsize=11, fontweight="bold")
        axes[3].set_ylabel("% / MB")
        axes[3].legend(["RAM (%)", "VRAM (MB)"], fontsize=8)
        axes[3].grid(axis="y", alpha=0.3)
    else:
        axes[3].text(0.5, 0.5, "chưa log tài nguyên\n(chạy train/eval với profiler)",
                     ha="center", va="center", transform=axes[3].transAxes)
        axes[3].set_title("Peak tài nguyên", fontsize=11, fontweight="bold")
    fig.suptitle(f"Độ phức tạp & tài nguyên — {name}", fontsize=14, fontweight="bold")
    _save(fig, f"fig12_complexity_{name}.png")
