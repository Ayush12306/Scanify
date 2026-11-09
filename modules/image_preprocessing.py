"""Validated image input and reusable preprocessing operations."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_FORMATS = {"JPEG", "PNG"}


def load_image(source: bytes | bytearray | str | Path, *, max_bytes: int = MAX_UPLOAD_BYTES) -> np.ndarray:
    """Decode an uploaded image as RGB uint8, applying EXIF orientation safely."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.stat().st_size > max_bytes:
            raise ValueError("Image exceeds the 20 MB upload limit.")
        data = path.read_bytes()
    else:
        data = bytes(source)
        if len(data) > max_bytes:
            raise ValueError("Image exceeds the 20 MB upload limit.")
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in ALLOWED_FORMATS:
                raise ValueError("Only JPEG and PNG images are supported.")
            if image.width < 32 or image.height < 32:
                raise ValueError("Image dimensions must be at least 32 × 32 pixels.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large to process safely.")
            rgb = ImageOps.exif_transpose(image).convert("RGB")
            return np.asarray(rgb, dtype=np.uint8).copy()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a valid, readable image.") from exc


def resize_image(image: np.ndarray, max_dimension: int = 1800) -> np.ndarray:
    if image is None or image.size == 0:
        raise ValueError("Cannot resize an empty image.")
    height, width = image.shape[:2]
    scale = min(1.0, max_dimension / max(height, width))
    if scale == 1:
        return image.copy()
    return cv2.resize(image, (max(1, round(width * scale)), max(1, round(height * scale))), interpolation=cv2.INTER_AREA)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image.copy()


def gaussian_smooth(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    kernel_size = max(1, int(kernel_size) | 1)
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def median_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    kernel_size = max(3, int(kernel_size) | 1)
    return cv2.medianBlur(image, kernel_size)


def bilateral_filter(image: np.ndarray, diameter: int = 9, sigma_color: float = 50, sigma_space: float = 50) -> np.ndarray:
    return cv2.bilateralFilter(image, diameter, sigma_color, sigma_space)


def normalize_image(image: np.ndarray) -> np.ndarray:
    return cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
