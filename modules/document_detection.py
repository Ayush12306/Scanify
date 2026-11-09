"""Contour-based document boundary detection and visualization."""
from __future__ import annotations

import cv2
import numpy as np

from .image_preprocessing import resize_image, to_grayscale


def order_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32).reshape(4, 2)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).ravel()
    return np.array([points[np.argmin(sums)], points[np.argmin(diffs)], points[np.argmax(sums)], points[np.argmax(diffs)]], dtype=np.float32)


def _valid_quad(points: np.ndarray, image_area: float) -> bool:
    if points.shape != (4, 2) or not np.isfinite(points).all():
        return False
    ordered = order_points(points)
    area = abs(cv2.contourArea(ordered))
    if area < image_area * 0.08:
        return False
    sides = [np.linalg.norm(ordered[(i + 1) % 4] - ordered[i]) for i in range(4)]
    return min(sides) > 20 and max(sides) / max(min(sides), 1) < 12


def detect_document(image: np.ndarray) -> np.ndarray | None:
    """Return ordered TL,TR,BR,BL corners in original-image coordinates, or None."""
    if image is None or image.size == 0:
        return None
    original_h, original_w = image.shape[:2]
    scale = min(1.0, 1400 / max(original_h, original_w))
    work = resize_image(image, 1400)
    gray = to_grayscale(work)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    edges = cv2.dilate(edges, kernel, iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
    work_area = float(work.shape[0] * work.shape[1])
    for contour in contours:
        if cv2.contourArea(contour) < work_area * 0.08:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4:
            candidate = order_points(approx.reshape(4, 2).astype(np.float32))
            if _valid_quad(candidate, work_area):
                return candidate / scale
    # Fallback: use the largest sufficiently large contour's convex hull rectangle only
    # when it has a clear four-sided approximation; never silently crop to the full frame.
    return None


def visualize_boundary(image: np.ndarray, corners: np.ndarray | None) -> np.ndarray:
    result = image.copy()
    if corners is not None:
        pts = np.round(order_points(corners)).astype(np.int32)
        cv2.polylines(result, [pts], True, (34, 128, 255), max(3, round(max(image.shape[:2]) / 400)), cv2.LINE_AA)
        for index, (x, y) in enumerate(pts):
            cv2.circle(result, (x, y), max(6, round(max(image.shape[:2]) / 150)), (104, 66, 220), -1, cv2.LINE_AA)
            cv2.putText(result, str(index + 1), (x + 8, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return result
