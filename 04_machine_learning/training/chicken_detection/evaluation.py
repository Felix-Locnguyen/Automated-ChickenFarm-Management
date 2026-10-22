# -*- coding: utf-8 -*-
"""
GĐ4 — ĐÁNH GIÁ mô hình:
  4A — Benchmark thủ công trên tập TEST:
       match GT → TP/FP/FN, P/R/F1; AP per class per IoU(0.5:0.05:0.95)
       → mAP@0.5, mAP@0.5:0.95; IoU trung bình 5 biến thể; CM + PR curve
  4B — Speed/Latency, Complexity (Params/FLOPs/size/peak RAM-VRAM),
       loss curves từ results.csv → validation_report.md
Số liệu tính THỦ CÔNG (không nhờ metric có sẵn của ultralytics).
"""
import math

import cv2
import numpy as np

from config import CLASS_NAMES, PERF_CSV, RUNS_DIR, YOLO_DIR, header, p
from encoding import load_gt
from report import write_report
from training import SystemProfiler
import viz


# ── Các biến thể IoU ──────────────────────────────────────────────────

def _xyxy_area(a):
    return max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])


def iou_metrics(A, B):
    """
    5 biến thể IoU cho 2 hộp A, B (xyxy, cùng hệ tọa độ pixel):
      IoU, GIoU, DIoU, CIoU, SIoU (Tong et al., 2023)
    Trả về dict — mỗi giá trị ∈ [-1, 1] (SIoU công thức tổng hợp 3 cost).
    """
    x1, y1 = max(A[0], B[0]), max(A[1], B[1])
    x2, y2 = min(A[2], B[2]), min(A[3], B[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = _xyxy_area(A) + _xyxy_area(B) - inter
    iou = inter / union if union > 0 else 0.0

    # khung bao ngoài nhỏ nhất C
    cx1, cy1 = min(A[0], B[0]), min(A[1], B[1])
    cx2, cy2 = max(A[2], B[2]), max(A[3], B[3])
    C_area = (cx2 - cx1) * (cy2 - cy1)
    # khoảng cách tâm
    acx, acy = (A[0] + A[2]) / 2, (A[1] + A[3]) / 2
    bcx, bcy = (B[0] + B[2]) / 2, (B[1] + B[3]) / 2
    rho2 = (acx - bcx) ** 2 + (acy - bcy) ** 2
    diag2 = (cx2 - cx1) ** 2 + (cy2 - cy1) ** 2  # |C|² (đường chéo khung bao)

    # GIoU = IoU - |C \ (A∪B)| / |C|
    enclose_free = C_area - union
    giou = iou - (enclose_free / C_area if C_area > 0 else 0.0)

    # DIoU = IoU - ρ²(tâm) / |C|²
    diou = iou - (rho2 / diag2 if diag2 > 0 else 0.0)

    # CIoU = DIoU - α·v ;  v = (4/π²)(atan(w'/h') - atan(w/h))²
    aw, ah = max(A[2] - A[0], 1e-9), max(A[3] - A[1], 1e-9)
    bw, bh = max(B[2] - B[0], 1e-9), max(B[3] - B[1], 1e-9)
    v = (4.0 / math.pi ** 2) * (math.atan(bw / bh) - math.atan(aw / ah)) ** 2
    alpha = v / ((1 - iou) + v) if (1 - iou) + v > 0 else 0.0
    ciou = diou - alpha * v

    # SIoU = IoU - (Λ + Δ + Ω)/2
    #   Λ (góc)        = 1 - 2·sin²(θ - π/4), θ = arcsin(min(dx,dy)/ρ) ∈ [0, π/4]
    #   Δ (khoảng cách) = 1 - exp(-2·(dw² + dh²))  (dw,dh chuẩn hóa theo ảnh)
    #   Ω (hình dạng)   = ((1-e^{-Jw})² + (1-e^{-Jh})²)/2
    dx, dy = abs(acx - bcx), abs(acy - bcy)
    rho = math.hypot(dx, dy)
    theta = math.asin(min(min(dx, dy) / rho, 1.0)) if rho > 0 else 0.0
    lam = 1.0 - 2.0 * math.sin(theta - math.pi / 4) ** 2
    delta = 1.0 - math.exp(-2.0 * (dx * dx + dy * dy) / max(diag2, 1e-9))
    jw, jh = abs(bw - aw) / bw, abs(bh - ah) / bh
    omega = ((1 - math.exp(-jw)) ** 2 + (1 - math.exp(-jh)) ** 2) / 2
    siou = iou - (lam + delta + omega) / 2.0

    return {"IoU": iou, "GIoU": giou, "DIoU": diou, "CIoU": ciou, "SIoU": siou}


def match_preds(preds, gts, iou_thr):
    """
    Matching greedy theo conf giảm dần: mỗi pred khớp GT chưa dùng, cùng class, IoU≥thr.
    preds: list[(xyxy, conf, cls)] | gts: list[(xyxy, cls)]
    → (tp_flags, matched_pairs{(pred_idx): gt_idx}, gt_used set, n_fn)
    """
    order = sorted(range(len(preds)), key=lambda i: -preds[i][1])
    gt_used = set()
    tp = [False] * len(preds)
    pairs = {}
    for pi in order:
        pbox, _, pcls = preds[pi]
        best_iou, best_g = iou_thr, -1
        for gi, (gbox, gcls) in enumerate(gts):
            if gi in gt_used or gcls != pcls:
                continue
            iou = iou_metrics(pbox, gbox)["IoU"]
            if iou >= best_iou:
                best_iou, best_g = iou, gi
        if best_g >= 0:
            tp[pi] = True
            gt_used.add(best_g)
            pairs[pi] = best_g
    n_fn = len(gts) - len(gt_used)
    return tp, pairs, gt_used, n_fn


def ap_all_points(tp_flags, confs, n_gt):
    """
    AP (all-point interpolation — kiểu COCO): sắp xếp theo conf giảm dần,
    tính P/R tích lũy, envelope tối đa, tích phân ∫ P dR.
    """
    if n_gt == 0:
        return 0.0, np.array([]), np.array([])
    idx = np.argsort(-np.asarray(confs))
    tp = np.asarray(tp_flags, dtype=float)[idx]
    ctp, cfp = np.cumsum(tp), np.cumsum(1 - tp)
    recall = ctp / n_gt
    precision = ctp / np.maximum(ctp + cfp, 1e-9)
    # envelope: precision không tăng (mặc định) — thêm điểm cuối
    mrec = np.concatenate([[0.0], recall, [recall[-1] if len(recall) else 0.0]])
    mpre = np.concatenate([[0.0], precision, [0.0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    ap = float(np.sum(np.diff(mrec) * mpre[1:]))
    return ap, precision, recall


# ── 4A — benchmark thủ công ───────────────────────────────────────────

def eval_test_set(args):
    """
    Predict toàn bộ ảnh test, match GT, tính metric + vẽ CM/PR/IoU.
    Trả về {tên model: dict số liệu}.
    """
    header("GIAI ĐOẠN 4A — BENCHMARK THỦ CÔNG TRÊN TẬP TEST")
    from ultralytics import YOLO

    test_img = YOLO_DIR / "test" / "images"
    test_lbl = YOLO_DIR / "test" / "labels"
    files = sorted(test_img.glob("*"))
    assert files, "Không có ảnh test — chạy --stage validate trước"

    per_model = {}
    for name in args.models:
        best = RUNS_DIR / name / "weights" / "best.pt"
        if not best.exists():
            p(f"[bỏ qua] {name}: chưa có {best}")
            continue
        p(f"\n── {name} ──")
        model = YOLO(str(best))
        all_preds, all_gts = [], []           # để tính AP/CM gộp
        cm = np.zeros((len(CLASS_NAMES) + 1, len(CLASS_NAMES) + 1), dtype=int)
        iou_sums = {k: 0.0 for k in ("IoU", "GIoU", "DIoU", "CIoU", "SIoU")}
        n_pairs = 0
        conf_thr = args.conf

        for f in files:
            img = cv2.imread(str(f))
            H, W = img.shape[:2]
            gts = load_gt(test_lbl / f"{f.stem}.txt", W, H)   # GT: YOLO → xyxy pixel

            # predict
            r = model.predict(str(f), conf=conf_thr, iou=0.5, verbose=False,
                              device=args.device)[0]
            preds = []
            if r.boxes is not None and len(r.boxes):
                b = r.boxes
                for xyxy, conf, cls in zip(b.xyxy.cpu().numpy(), b.conf.cpu().numpy(),
                                           b.cls.cpu().numpy()):
                    preds.append((tuple(xyxy), float(conf), int(cls)))

            tp, pairs, gt_used, n_fn = match_preds(preds, gts, 0.5)
            # CM: cột = pred, hàng = GT (background = lớp cuối)
            for pi, ti in enumerate(tp):
                pc = preds[pi][2]
                if ti:
                    cm[gts[pairs[pi]][1], pc] += 1
                else:
                    cm[len(CLASS_NAMES), pc] += 1           # FP (GT = background)
            for gi in range(len(gts)):
                if gi not in gt_used:
                    cm[gts[gi][1], len(CLASS_NAMES)] += 1    # FN (pred = background)
            # IoU variants trên cặp match
            for pi, gi in pairs.items():
                for k, v in iou_metrics(preds[pi][0], gts[gi][0]).items():
                    iou_sums[k] += v
                n_pairs += 1
            all_preds.append((preds, tp))
            all_gts.append(gts)

        # ── P/R/FN gộp
        n_tp = sum(int(t) for _, tp in all_preds for t in tp)
        n_fp = sum(len(pd_) - int(sum(tp)) for pd_, tp in all_preds)
        n_gt = sum(len(g) for g in all_gts)
        n_fn = n_gt - n_tp
        precision = n_tp / max(n_tp + n_fp, 1e-9)
        recall = n_tp / max(n_tp + n_fn, 1e-9)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)

        # ── mAP50 + mAP50-95 (per class, per IoU threshold)
        aps50, aps95 = [], []
        for thr in np.arange(0.5, 0.951, 0.05):
            cls_aps = []
            for cid in CLASS_NAMES:
                n_gt_c = sum(1 for gts in all_gts for g in gts if g[1] == cid)
                # gộp detections per class, matching lại theo thr hiện tại
                det_tps, det_confs = [], []
                for (preds, _), gts in zip(all_preds, all_gts):
                    cls_preds = [(i, pr) for i, pr in enumerate(preds) if pr[2] == cid]
                    cls_gts = [(gi, g) for gi, g in enumerate(gts) if g[1] == cid]
                    used = set()
                    for i, pr in sorted(cls_preds, key=lambda x: -x[1][1]):
                        best_i, best_iou = -1, thr
                        for gi, g in cls_gts:
                            if gi in used:
                                continue
                            iou = iou_metrics(pr[0], g[0])["IoU"]
                            if iou >= best_iou:
                                best_i, best_iou = gi, iou
                        if best_i >= 0:
                            used.add(best_i)
                        det_tps.append(best_i >= 0)
                        det_confs.append(pr[1])
                ap, _, _ = ap_all_points(det_tps, det_confs, n_gt_c)
                cls_aps.append(ap)
            m = float(np.mean(cls_aps)) if cls_aps else 0.0
            if abs(thr - 0.5) < 1e-6:
                aps50.append(m)
            aps95.append(m)
        map50 = aps50[0]
        map95 = float(np.mean(aps95))

        # ── biểu đồ CM + IoU variants
        viz.confusion_chart(cm, name, conf_thr)
        iou_avg = {k: v / max(n_pairs, 1) for k, v in iou_sums.items()}
        viz.iou_chart(iou_avg, name)

        # ── PR curve (gộp detections match @0.5, sort conf giảm dần)
        det = []
        for (preds, _), gts in zip(all_preds, all_gts):
            tp, _, _, _ = match_preds(preds, gts, 0.5)
            det.extend((pr[1], t) for pr, t in zip(preds, tp))
        if det:
            det.sort(key=lambda x: -x[0])
            tps = np.array([d[1] for d in det], dtype=float)
            ctp, cfp = np.cumsum(tps), np.cumsum(1 - tps)
            rec = ctp / max(n_gt, 1)
            prec = ctp / np.maximum(ctp + cfp, 1e-9)
            f1c = 2 * prec * rec / np.maximum(prec + rec, 1e-9)
            i_best = int(np.argmax(f1c))
            viz.pr_chart(rec, prec, i_best, float(f1c[i_best]), det[i_best][0], name)

        p(f"  TP/FP/FN = {n_tp}/{n_fp}/{n_fn} | P={precision:.3f} R={recall:.3f} F1={f1:.3f}")
        p(f"  mAP@0.5={map50:.3f} | mAP@0.5:0.95={map95:.3f}")
        p("  IoU variants: " + " | ".join(f"{k}={v:.3f}" for k, v in iou_avg.items()))
        per_model[name] = dict(tp=n_tp, fp=n_fp, fn=n_fn, precision=precision,
                               recall=recall, f1=f1, map50=map50, map95=map95,
                               iou_avg=iou_avg, n_pairs=n_pairs)

    return per_model


# ── 4B — speed, complexity, báo cáo ───────────────────────────────────

def speed_benchmark(model, name, args):
    """
    Speed & Latency: warmup + N ảnh (100–500, lấy từ train, cycling nếu thiếu).
    Mỗi ảnh: results.speed = {'preprocess', 'inference', 'postprocess'} (ms).
    → trung bình từng bước, tổng latency, FPS + bar chart.
    """
    import torch
    files = sorted((YOLO_DIR / "train" / "images").glob("*"))
    n = max(100, min(500, args.speed_images))
    seq = [files[i % len(files)] for i in range(n)]
    warmup = 20

    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()

    rows = []
    for i, f in enumerate(seq):
        r = model.predict(str(f), conf=args.conf, iou=0.5, verbose=False,
                          device=args.device)[0]
        if i >= warmup:                      # 20 lần đầu = warmup, không tính
            rows.append(r.speed)             # ms: preprocess / inference / postprocess
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    def stat(k):
        v = np.array([x[k] for x in rows], dtype=float)
        return float(v.mean()), float(v.std())

    pre_m, pre_s = stat("preprocess")
    inf_m, inf_s = stat("inference")
    post_m, post_s = stat("postprocess")
    total = pre_m + inf_m + post_m
    fps = 1000.0 / total if total > 0 else 0.0
    peak_vram = torch.cuda.max_memory_allocated() / 2**20 if torch.cuda.is_available() else 0.0

    p(f"\n── Speed — {name} ({len(rows)} ảnh, warmup {warmup}) ──")
    p(f"  Pre-process : {pre_m:.2f} ± {pre_s:.2f} ms")
    p(f"  Inference   : {inf_m:.2f} ± {inf_s:.2f} ms")
    p(f"  Post/NMS    : {post_m:.2f} ± {post_s:.2f} ms")
    p(f"  Tổng latency: {total:.2f} ms → FPS ≈ {fps:.1f}")
    p(f"  Peak VRAM   : {peak_vram:.0f} MB (benchmark)")

    sp = dict(pre=pre_m, inf=inf_m, post=post_m, total=total, fps=fps, n=len(rows))
    viz.speed_chart(sp, name)
    return sp


def complexity_stats(model, name, perf_df):
    """
    Complexity & Resource:
      - Parameters, GFLOPs (ultralytics), size best.pt (MB)
      - Peak RAM / VRAM (lấy max từ system_performance_log.csv của model này)
    """
    from ultralytics.utils.torch_utils import get_flops, get_num_params

    core = model.model
    params = get_num_params(core)
    try:
        flops_g = float(get_flops(core, 640))
    except Exception:
        flops_g = float("nan")
    pt_path = RUNS_DIR / name / "weights" / "best.pt"
    size_mb = pt_path.stat().st_size / 2**20 if pt_path.exists() else 0.0

    peak_ram = peak_gpu = peak_vram = float("nan")
    if perf_df is not None and len(perf_df):
        sub = perf_df[perf_df["model"].astype(str) == name]
        if len(sub):
            peak_ram = sub["ram_pct"].astype(float).max()
            gpu_col = sub["gpu_util_pct"].replace("", np.nan).astype(float)
            vram_col = sub["vram_used_mb"].replace("", np.nan).astype(float)
            peak_gpu = float(gpu_col.max()) if gpu_col.notna().any() else float("nan")
            peak_vram = float(vram_col.max()) if vram_col.notna().any() else float("nan")

    stats = dict(params=params, flops_g=flops_g, size_mb=size_mb,
                 peak_ram_pct=peak_ram, peak_gpu_pct=peak_gpu, peak_vram_mb=peak_vram)
    p(f"\n── Complexity — {name} ──")
    p(f"  Parameters : {params:,} ({params / 1e6:.2f} M)")
    p(f"  FLOPs      : {flops_g:.2f} GFLOPs @imgsz=640")
    p(f"  Weights    : {size_mb:.1f} MB ({pt_path.name})")
    p(f"  Peak RAM   : {peak_ram:.0f}% | Peak GPU util: {peak_gpu:.0f}% | "
      f"Peak VRAM: {peak_vram:.0f} MB")
    viz.complexity_chart(stats, name)
    return stats


def stage4_eval(args):
    """Toàn bộ GĐ4: benchmark test → loss curves → speed → complexity → báo cáo."""
    header("GIAI ĐOẠN 4 — ĐÁNH GIÁ CHI TIẾT")
    from ultralytics import YOLO
    import pandas as pd

    per_model = eval_test_set(args)

    extras = {"models": args.models, "train_rows": {}, "speed": {}, "complexity": {}}
    perf_df = pd.read_csv(PERF_CSV) if PERF_CSV.exists() else None

    for name in args.models:
        if not (RUNS_DIR / name / "weights" / "best.pt").exists():
            continue
        # loss curves + kết quả epoch cuối
        df = viz.training_curves(name)
        if df is not None:
            last = df.iloc[-1]
            ecol = viz.find_col(df, "epoch")
            mcol = viz.find_col(df, "metrics/mAP50-95(B)", "metrics/mAP50-95")
            extras["train_rows"][name] = (
                f"{int(df[ecol].iloc[-1])} epochs"
                + (f", mAP50-95={last[mcol]:.3f}" if mcol else ""))
        # speed + complexity (profiler log song song để bắt peak RAM/VRAM)
        model = YOLO(str(RUNS_DIR / name / "weights" / "best.pt"))
        profiler = SystemProfiler(interval=args.prof_interval, stage="eval", model=name)
        profiler.start()
        extras["speed"][name] = speed_benchmark(model, name, args)
        profiler.stop()
        extras["complexity"][name] = complexity_stats(model, name, perf_df)

    write_report(per_model, extras)
    header("GĐ4 HOÀN TẤT — xem evaluation/validation_report.md")
