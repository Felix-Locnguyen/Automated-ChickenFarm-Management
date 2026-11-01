# -*- coding: utf-8 -*-
"""
GĐ3 — HUẤN LUYỆN YOLO26 (nano + small):
  - Bảng siêu tham số + xác nhận [Y/n] (INTERACTIVE_MODE)
  - Tự detect thiết bị (CUDA/GPU, CPU; TPU không khả dụng)
  - Thread nền ghi CPU/RAM/GPU/VRAM mỗi N giây → system_performance_log.csv
"""
import csv
import threading
import time

from config import (AUG_PROBS, DATA_YAML, INTERACTIVE_MODE, PERF_CSV, RUNS_DIR,
                    header, p)
from features import install_augmentation


class SystemProfiler(threading.Thread):
    """
    Luồng nền (daemon) ghi định kỳ CPU %, RAM %, GPU Util %, VRAM MB
    vào system_performance_log.csv. Dùng psutil + pynvml (nvidia-ml-py).
    """

    def __init__(self, interval=3.0, stage="train", model=""):
        super().__init__(daemon=True)
        self.interval, self.stage, self.model = interval, stage, model
        self._stop = threading.Event()
        self.peak = {"cpu": 0.0, "ram": 0.0, "gpu": 0.0, "vram_mb": 0.0}
        self._nvml_ok = False
        try:
            import pynvml
            pynvml.nvmlInit()
            self._pynvml = pynvml
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self._nvml_ok = True
        except Exception as e:
            p(f"[profiler] pynvml không khả dụng ({e}) — sẽ log CPU/RAM thôi")

    def run(self):
        import psutil
        psutil.cpu_percent()          # lần đầu trả về 0 → khởi tạo
        new_file = not PERF_CSV.exists() or PERF_CSV.stat().st_size == 0
        with open(PERF_CSV, "a", newline="") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["timestamp", "stage", "model", "cpu_pct", "ram_pct",
                            "gpu_util_pct", "vram_used_mb", "vram_total_mb"])
            while not self._stop.is_set():
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                gpu = vram_used = vram_total = ""
                if self._nvml_ok:
                    try:
                        gpu = self._pynvml.nvmlDeviceGetUtilizationRates(self._handle).gpu
                        mi = self._pynvml.nvmlDeviceGetMemoryInfo(self._handle)
                        vram_used, vram_total = mi.used // 2**20, mi.total // 2**20
                    except Exception:
                        pass
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), self.stage, self.model,
                            cpu, ram, gpu, vram_used, vram_total])
                f.flush()
                self.peak["cpu"] = max(self.peak["cpu"], float(cpu))
                self.peak["ram"] = max(self.peak["ram"], float(ram))
                if gpu != "":
                    self.peak["gpu"] = max(self.peak["gpu"], float(gpu))
                    self.peak["vram_mb"] = max(self.peak["vram_mb"], float(vram_used))
                self._stop.wait(self.interval)

    def stop(self):
        self._stop.set()
        self.join(timeout=5)
        if self._nvml_ok:
            try:
                self._pynvml.nvmlShutdown()
            except Exception:
                pass


def detect_device():
    """In + trả thiết bị train (0 = GPU CUDA, 'cpu' = CPU)."""
    import torch
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        total = torch.cuda.get_device_properties(0).total_memory / 2**30
        p(f"Thiết bị : CUDA / GPU — {name} ({total:.1f} GB VRAM)")
        p(f"CUDA     : {torch.version.cuda}")
        p("TPU      : không khả dụng (máy này chỉ có CUDA/CPU)")
        return 0
    p("Thiết bị : CPU (CUDA không khả dụng)")
    return "cpu"


def confirm_train(args):
    """In bảng siêu tham số + hỏi [Y/n] nếu INTERACTIVE_MODE. Trả về True nếu đồng ý."""
    rows = [
        ("models", ", ".join(args.models)),
        ("epochs", args.epochs),
        ("batch_size", args.batch),
        ("imgsz", args.imgsz),
        ("lr0 (learning rate)", args.lr0),
        ("optimizer", args.optimizer),
        ("patience (chống overfit)", args.patience),
        ("seed", args.seed),
        ("conf (ngưỡng eval)", args.conf),
        ("aug gray/warm/noise", f"{AUG_PROBS['gray']}/{AUG_PROBS['warm']}/{AUG_PROBS['noise']}"),
        ("INTERACTIVE_MODE", INTERACTIVE_MODE and not args.no_interactive),
        ("output", str(RUNS_DIR)),
    ]
    p("\n┌── BẢNG SIÊU THAM SỐ HUẤN LUYỆN " + "─" * 40)
    for k, v in rows:
        p(f"│  {k:<28}: {v}")
    p("└" + "─" * 66)
    if INTERACTIVE_MODE and not args.no_interactive:
        ans = input("  Nhấn Y để bắt đầu train [Y/n]: ").strip().lower()
        if ans not in ("", "y", "yes"):
            p("→ Hủy train.")
            return False
    return True


def stage3_train(args):
    """Train lần lượt các model trong args.models → runs/<tên>/weights/best.pt."""
    header("GIAI ĐOẠN 3 — HUẤN LUYỆN MÔ HÌNH")
    assert DATA_YAML.exists(), "Thiếu data.yaml — chạy --stage validate trước"
    if not confirm_train(args):
        return

    from ultralytics import YOLO        # import nặng → để trong hàm

    device = detect_device()
    install_augmentation()              # gắn PhotometricAug vào pipeline ultralytics

    train_args = dict(
        data=str(DATA_YAML), epochs=args.epochs, batch=args.batch, imgsz=args.imgsz,
        lr0=args.lr0, optimizer=args.optimizer, patience=args.patience, seed=args.seed,
        workers=args.workers, amp=True, project=str(RUNS_DIR), exist_ok=True,
        verbose=True, device=device,
    )

    for name in args.models:
        header(f"TRAIN {name}")
        profiler = SystemProfiler(interval=args.prof_interval, stage="train", model=name)
        profiler.start()
        t0 = time.time()
        try:
            model = YOLO(f"{name}.pt")      # tự tải weight pretrained từ GitHub
            model.train(**train_args, name=name)
        except Exception as e:
            profiler.stop()
            p(f"[LỖI] train {name}: {e}")
            continue
        profiler.stop()

        run_dir = RUNS_DIR / name
        p(f"\n✓ {name} xong trong {(time.time() - t0) / 60:.1f} phút → {run_dir}")
        p(f"  best: {run_dir / 'weights' / 'best.pt'} | results: {run_dir / 'results.csv'}")
        p(f"  Peak: CPU {profiler.peak['cpu']:.0f}% | RAM {profiler.peak['ram']:.0f}% | "
          f"GPU {profiler.peak['gpu']:.0f}% | VRAM {profiler.peak['vram_mb']:.0f} MB")
        # val cuối bằng best.pt
        try:
            v = YOLO(str(run_dir / "weights" / "best.pt")).val(
                data=str(DATA_YAML), split="val", verbose=False, device=device)
            p(f"  val cuối: mAP50={v.box.map50:.3f} | mAP50-95={v.box.map:.3f} "
              f"| P={v.box.mp:.3f} | R={v.box.mr:.3f}")
        except Exception as e:
            p(f"  (không chạy được val cuối: {e})")
    header("GĐ3 HOÀN TẤT")
