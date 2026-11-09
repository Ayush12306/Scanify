"""Perspective correction using a four-point projective transform."""
from __future__ import annotations

import cv2
import numpy as np

from .document_detection import order_points


def four_point_transform(image: np.ndarray, corners: np.ndarray, max_dimension: int = 4000) -> np.ndarray:
    points = order_points(corners)
    tl, tr, br, bl = points
    width = max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl))
    height = max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl))
    out_w, out_h = int(round(width)), int(round(height))
    if out_w < 2 or out_h < 2:
        raise ValueError("Selected corners do not define a usable document.")
    scale = min(1.0, max_dimension / max(out_w, out_h))
    out_w, out_h = max(2, round(out_w * scale)), max(2, round(out_h * scale))
    destination = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(points.astype(np.float32), destination)
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-12:
        raise ValueError("Could not compute a stable perspective correction.")
    return cv2.warpPerspective(image, matrix, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
