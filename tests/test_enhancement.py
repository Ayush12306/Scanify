import numpy as np

from modules.image_enhancement import enhance_image
from modules.image_quality import assess_quality
from modules.shadow_removal import remove_shadows


def test_enhancement_modes_return_valid_arrays():
    image = np.full((120, 160, 3), 220, dtype=np.uint8)
    image[50:58, 25:135] = 30
    for mode in ["Original", "Color", "Grayscale", "Black & White", "Document Clean", "Sharpen", "High Contrast"]:
        result = enhance_image(image, mode, brightness=5, contrast=1.1)
        assert result.size > 0
        assert result.dtype == np.uint8


def test_shadow_removal_and_quality_report():
    image = np.tile(np.linspace(80, 200, 120, dtype=np.uint8), (160, 1))
    rgb = np.repeat(image[:, :, None], 3, axis=2)
    corrected = remove_shadows(rgb)
    assert corrected.shape == rgb.shape
    report = assess_quality(rgb)
    assert report["width"] == 120
    assert report["height"] == 160
    assert report["suggestions"]
