"""tests rio_cogeo.cogeo."""

import os

from rio_cogeo.utils import get_overview_level

raster_path_rgb = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgb.tif")


def test_overviewlevel_valid():
    """Should work as expected (return overview level)."""
    assert get_overview_level(raster_path_rgb, 128) == 2
