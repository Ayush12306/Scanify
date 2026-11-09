"""Heuristic image-quality measurements and suggestions."""
from __future__ import annotations

import cv2
import numpy as np


def assess_quality(image: np.ndarray) -> dict:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    smooth = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = float(np.mean(np.abs(gray.astype(np.float32) - smooth.astype(np.float32))))
    suggestions = []
    if blur < 80:
        suggestions.append("Image appears blurry; retake the photo with steadier focus.")
    if brightness < 75:
        suggestions.append("Document may be too dark; add more even lighting.")
    if brightness > 220:
        suggestions.append("Highlights may be overexposed; reduce glare or move the light source.")
    if contrast < 30:
        suggestions.append("Lighting or text contrast is low; try a high-contrast enhancement.")
    if min(gray.shape[:2]) < 600:
        suggestions.append("Resolution is low; use a larger image for better readability.")
    if not suggestions:
        suggestions.append("No major issues detected by these heuristic checks.")
    return {"width": int(image.shape[1]), "height": int(image.shape[0]), "brightness": brightness, "contrast": contrast, "blur_score": blur, "noise_estimate": noise, "suggestions": suggestions}
