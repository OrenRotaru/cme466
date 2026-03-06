from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def ensure_uint8(img: np.ndarray) -> np.ndarray:
    if img.dtype == np.uint8:
        return img
    return np.clip(img, 0, 255).astype(np.uint8)


def ensure_bgr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.ndim == 3 and img.shape[2] == 3:
        return img
    raise ValueError("Expected image with shape HxW or HxWx3")


def ensure_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    if img.ndim == 3 and img.shape[2] == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    raise ValueError("Expected image with shape HxW or HxWx3")


def odd_ksize(value: Any, min_odd: int = 1) -> int:
    k = int(value)
    if k < min_odd:
        k = min_odd
    if k % 2 == 0:
        k += 1
    return k


def gamma_correct(img: np.ndarray, gamma: float) -> np.ndarray:
    gamma = max(0.01, float(gamma))
    lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(ensure_uint8(img), lut)
