"""Reusable scan processing helpers."""
from __future__ import annotations

import numpy as np

from modules.document_detection import detect_document
from modules.image_enhancement import enhance_image
from modules.perspective_transform import four_point_transform


def process_scan(image: np.ndarray, mode: str = "Original", corners: np.ndarray | None = None, *, rectify: bool = True, **settings) -> tuple[np.ndarray, np.ndarray | None]:
    selected = corners if corners is not None else detect_document(image)
    source = four_point_transform(image, selected) if rectify and selected is not None else image.copy()
    return enhance_image(source, mode, **settings), selected
