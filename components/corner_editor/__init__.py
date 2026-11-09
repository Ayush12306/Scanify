"""A tiny local Streamlit component for interactive draggable document corners."""
from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_COMPONENT = components.declare_component(
    "scanify_corner_editor",
    path=str(Path(__file__).parent / "frontend"),
)


def corner_editor(image_base64: str, width: int, height: int, default_corners: list[list[float]], *, key: str) -> list[list[float]] | None:
    """Display an image and return four normalized, user-adjustable corner points."""
    value = _COMPONENT(image_base64=image_base64, image_width=width, image_height=height,
                       default_corners=default_corners, key=key, default=None)
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        points = [[float(point[0]), float(point[1])] for point in value]
    except (TypeError, ValueError, IndexError):
        return None
    return points
