"""Uneven-illumination correction using a large morphological background estimate."""
from __future__ import annotations

import cv2
import numpy as np


def remove_shadows(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        channels = [image]
        was_gray = True
    else:
        channels = cv2.split(image)
        was_gray = False
    corrected = []
    h, w = image.shape[:2]
    kernel_size = max(15, (min(h, w) // 20) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    for channel in channels:
        background = cv2.morphologyEx(channel, cv2.MORPH_CLOSE, kernel)
        normalized = cv2.divide(channel, np.maximum(background, 1), scale=255)
        corrected.append(cv2.normalize(normalized, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8))
    result = corrected[0] if was_gray else cv2.merge(corrected)
    return result
