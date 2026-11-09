"""Optional local Tesseract OCR integration."""
from __future__ import annotations

import shutil

import cv2
import numpy as np
import pytesseract


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def available_languages() -> list[str]:
    if not tesseract_available():
        return []
    try:
        return sorted(pytesseract.get_languages(config=""))
    except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError):
        return []


def extract_text(image: np.ndarray, language: str = "eng") -> str:
    if not tesseract_available():
        raise RuntimeError("Tesseract OCR is not installed or is not on PATH. Install Tesseract, then restart Scanify.")
    try:
        return pytesseract.image_to_string(image, lang=language, config="--psm 6").strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("Tesseract OCR could not be found. Install it and restart Scanify.") from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError(f"OCR failed: {exc}") from exc
