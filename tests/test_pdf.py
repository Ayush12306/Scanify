from io import BytesIO

import numpy as np
from pypdf import PdfReader

from modules.pdf_generator import generate_pdf


def test_single_and_multi_page_pdf():
    portrait = np.full((100, 70, 3), 245, dtype=np.uint8)
    landscape = np.full((60, 120, 3), 210, dtype=np.uint8)
    single = generate_pdf([portrait])
    multiple = generate_pdf([portrait, landscape])
    assert PdfReader(BytesIO(single)).get_num_pages() == 1
    assert PdfReader(BytesIO(multiple)).get_num_pages() == 2
