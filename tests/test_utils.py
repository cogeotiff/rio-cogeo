"""tests rio_cogeo.cogeo."""

import os

import rasterio
from rio_cogeo import utils

raster_path_rgb = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgb.tif")
raster_path_rgba = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgba.tif")
raster_path_noweb = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_noweb.tif"
)


def test_overviewlevel_valid():
    """Should work as expected (return overview level)."""
    assert utils.get_maximum_overview_level(raster_path_rgb, 128) == 2


def test_alpha_band_valid():
    """Should work as expected."""
    with rasterio.open(raster_path_rgb) as src:
        assert not utils.has_alpha_band(src)

    with rasterio.open(raster_path_rgba) as src:
        assert utils.has_alpha_band(src)


def test_max_zoom():
    """Should work as expected."""
    with rasterio.open(raster_path_noweb) as src:
        assert utils.get_max_zoom(src) == 18
        assert utils.get_max_zoom(src, snap=0) == 19
        assert utils.get_max_zoom(src, snap=1) == 18


def test_meters_per_pixel():
    """Should work as expected."""
    assert int(utils._meters_per_pixel(10, 0)) == 152
    assert int(utils._meters_per_pixel(10, 45)) == 108
    assert int(utils._meters_per_pixel(10, -45)) == 108
