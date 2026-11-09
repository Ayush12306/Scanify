"""Aspect-ratio-preserving single and multi-page PDF generation."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def generate_pdf(images: Sequence[np.ndarray], output: str | Path | None = None, margin: float = 28) -> bytes:
    if not images:
        raise ValueError("At least one page is required to create a PDF.")
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=1)
    page_w, page_h = A4
    for array in images:
        image = Image.fromarray(array.astype(np.uint8))
        width, height = image.size
        usable_w, usable_h = page_w - 2 * margin, page_h - 2 * margin
        if width > height:
            pw, ph = landscape(A4)
            pdf.setPageSize((pw, ph))
            usable_w, usable_h = pw - 2 * margin, ph - 2 * margin
        else:
            pw, ph = portrait(A4)
            pdf.setPageSize((pw, ph))
            usable_w, usable_h = pw - 2 * margin, ph - 2 * margin
        scale = min(usable_w / width, usable_h / height)
        draw_w, draw_h = width * scale, height * scale
        x, y = (pw - draw_w) / 2, (ph - draw_h) / 2
        pdf.drawImage(ImageReader(image), x, y, draw_w, draw_h, preserveAspectRatio=True, mask="auto")
        pdf.showPage()
    pdf.save()
    data = buffer.getvalue()
    if output is not None:
        Path(output).write_bytes(data)
    return data
