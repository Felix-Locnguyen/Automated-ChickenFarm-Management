# -*- coding: utf-8 -*-
"""
GĐ2 — TẠO ĐẶC TRƯNG & TĂNG CƯỜNG (augmentation ĐỘNG lúc train):
  gray  — ảnh xám (giữ 3 kênh)
  warm  — ánh sáng ấm (mô phỏng đèn sưởi IR)
  noise — nhiễu Gaussian
Áp DỤNG THEO XÁC SUẤT trong RAM của DataLoader — KHÔNG ghi đè ảnh gốc.
Chỉ đổi pixel (không đổi hình học) → bbox giữ nguyên.
"""
import random

import numpy as np
import albumentations as A

from config import AUG_PROBS


class PhotometricAug:
    """3 phép tăng cường ảnh, mỗi phép 1 lần thử theo xác suất."""

    def __init__(self,
                 p_gray=AUG_PROBS["gray"],
                 p_warm=AUG_PROBS["warm"],
                 p_noise=AUG_PROBS["noise"]):
        self.p_gray, self.p_warm, self.p_noise = p_gray, p_warm, p_noise
        self._gray = A.ToGray(num_output_channels=3, p=1.0)      # albumentations 2.x
        self._noise = A.GaussNoise(std_range=(0.04, 0.18), p=1.0)

    def __call__(self, sample):
        """
        Hook cho pipeline transform của ultralytics:
        sample = dict có key 'img' (np.uint8 HWC) — chạy TRƯỚC transform 'Format'.
        """
        img = sample["img"]
        if random.random() < self.p_gray:
            img = self._gray(image=img)["image"]
        if random.random() < self.p_warm:
            img = self.warm(img)
        if random.random() < self.p_noise:
            img = self._noise(image=img)["image"]
        sample["img"] = img
        return sample

    @staticmethod
    def warm(img):
        """Nhân channel: đỏ ↑ xanh ↓ → tông vàng ấm (giống đèn sưởi)."""
        tint = np.array([1.15, 1.0, 0.82], np.float32)
        return np.clip(img.astype(np.float32) * tint, 0, 255).astype(np.uint8)

    def apply(self, img, mode):
        """Áp 1 phép CỐ ĐỊNH cho stage 'aug' xem trước — mode ∈ {gray, warm, noise}."""
        if mode == "gray":
            return self._gray(image=img)["image"]
        if mode == "warm":
            return self.warm(img)
        if mode == "noise":
            return self._noise(image=img)["image"]
        raise ValueError(mode)


def install_augmentation():
    """
    Gắn PhotometricAug vào YOLODataset.build_transforms (MONKEYPATCH method).
    Không tạo class con — Python 3.14 dùng 'forkserver', class local không pickle
    được cho DataLoader worker (đã từng làm train fail).
    Chèn TRƯỚC transform cuối ('Format') — lúc đó 'img' vẫn là numpy uint8.
    Val/test (augment=False) → không tác động.
    """
    from ultralytics.data.dataset import YOLODataset   # import nặng → để trong hàm

    if getattr(YOLODataset, "_chicken_aug_installed", False):
        return

    orig_build = YOLODataset.build_transforms         # giữ method gốc

    def _build_transforms(self, hyp):
        transforms = orig_build(self, hyp)
        if getattr(self, "augment", False) and transforms.transforms:
            transforms.insert(len(transforms.transforms) - 1, PhotometricAug())
        return transforms

    YOLODataset.build_transforms = _build_transforms
    YOLODataset._chicken_aug_installed = True
