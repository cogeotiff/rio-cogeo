"""tests rio_cogeo.cogeo."""

import os

import pytest
import rasterio

from rio_cogeo.errors import DeprecationWarning
from rio_cogeo.utils import get_maximum_overview_level

raster_path_rgb = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgb.tif")


def test_overviewlevel_valid():
    """Should work as expected (return overview level)."""
    with pytest.warns(DeprecationWarning):
        with rasterio.open(raster_path_rgb) as src_dst:
            assert get_maximum_overview_level(src_dst, 128) == 2
            assert get_maximum_overview_level(src_dst) == 0
