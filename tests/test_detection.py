import cv2
import numpy as np
import pytest
from PIL import Image
from io import BytesIO

from modules.document_detection import detect_document
from modules.image_preprocessing import load_image, to_grayscale
from modules.perspective_transform import four_point_transform


def synthetic_page():
    image = np.zeros((500, 700, 3), dtype=np.uint8)
    cv2.fillConvexPoly(image, np.array([[130, 55], [570, 80], [535, 440], [95, 410]], np.int32), (245, 245, 245))
    cv2.putText(image, "SCANIFY TEST", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (20, 20, 20), 2)
    return image


def test_load_rgb_image_and_invalid_image():
    buff = BytesIO()
    Image.fromarray(np.full((80, 120, 3), 100, np.uint8)).save(buff, format="PNG")
    loaded = load_image(buff.getvalue())
    assert loaded.shape == (80, 120, 3)
    assert loaded.dtype == np.uint8
    with pytest.raises(ValueError):
        load_image(b"not an image")


def test_detect_document_and_transform():
    image = synthetic_page()
    corners = detect_document(image)
    assert corners is not None
    assert corners.shape == (4, 2)
    corrected = four_point_transform(image, corners)
    assert corrected.shape[0] > 200
    assert corrected.shape[1] > 200


def test_no_document_returns_none():
    assert detect_document(np.zeros((160, 240, 3), dtype=np.uint8)) is None


def test_grayscale_conversion():
    gray = to_grayscale(np.zeros((20, 30, 3), dtype=np.uint8))
    assert gray.shape == (20, 30)
