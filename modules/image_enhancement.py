"""Classical image enhancement modes with adjustable controls."""
from __future__ import annotations

import cv2
import numpy as np

MODES = ["Original", "Color", "Grayscale", "Black & White", "Document Clean", "Sharpen", "High Contrast"]


def enhance_image(image: np.ndarray, mode: str = "Original", *, brightness: int = 0, contrast: float = 1.0, sharpness: float = 0.0, denoise: int = 0, shadow_removal: bool = False) -> np.ndarray:
    if image is None or image.size == 0:
        raise ValueError("Cannot enhance an empty image.")
    result = image.copy()
    if denoise > 0:
        strength = int(np.clip(denoise, 0, 10) * 2)
        result = cv2.fastNlMeansDenoisingColored(result, None, strength, strength, 7, 21)
    if shadow_removal:
        from .shadow_removal import remove_shadows
        result = remove_shadows(result)
    if mode == "Grayscale":
        result = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
    elif mode == "Black & White":
        gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY) if result.ndim == 3 else result
        result = cv2.adaptiveThreshold(cv2.GaussianBlur(gray, (5, 5), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
    elif mode == "Document Clean":
        gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY) if result.ndim == 3 else result
        gray = cv2.medianBlur(gray, 3)
        result = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 12)
    elif mode == "Sharpen":
        blurred = cv2.GaussianBlur(result, (0, 0), 2)
        result = cv2.addWeighted(result, 1.6, blurred, -0.6, 0)
    elif mode == "High Contrast":
        gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY) if result.ndim == 3 else result
        result = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    elif mode not in {"Original", "Color"}:
        raise ValueError(f"Unknown enhancement mode: {mode}")
    if result.ndim == 2 and mode in {"Original", "Color"}:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2RGB)
    if mode not in {"Black & White", "Document Clean"}:
        result = cv2.convertScaleAbs(result, alpha=float(np.clip(contrast, 0.2, 3.0)), beta=int(np.clip(brightness, -100, 100)))
    if sharpness > 0:
        amount = float(np.clip(sharpness, 0, 3))
        blur = cv2.GaussianBlur(result, (0, 0), 1.5)
        result = cv2.addWeighted(result, 1 + amount, blur, -amount, 0)
    return result
