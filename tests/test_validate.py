"""tests rio_cogeo.cogeo."""

import os

import pytest
from click.testing import CliRunner

from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles

fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures")

raster_rgb = os.path.join(fixture_dir, "image_rgb.tif")
raster_external = os.path.join(fixture_dir, "validate", "image_external.tif")
raster_no_ovr = os.path.join(fixture_dir, "validate", "image_no_overview.tif")
raster_ovrsorted = os.path.join(fixture_dir, "validate", "image_sorted.tif")
raster_decim = os.path.join(fixture_dir, "validate", "image_dec.tif")
raster_jpeg = os.path.join(fixture_dir, "validate", "nontiff.jpg")
raster_big = os.path.join(fixture_dir, "image_2000px.tif")

# COG created with rio-cogeo but using gdal 3.1
raster_rioCOGgdal31 = os.path.join(fixture_dir, "validate", "image_rioCOG_gdal3.1.tif")

# COG created using GDAL COG Driver
raster_COGgdal31 = os.path.join(fixture_dir, "validate", "image_rioCOG_gdal3.1.tif")

jpeg_profile = cog_profiles.get("jpeg")
jpeg_profile.update({"blockxsize": 256, "blockysize": 256})


def test_cog_validate_valid(monkeypatch):
    """Should work as expected (validate cogeo file)."""
    # not tiled but 512x512
    assert cog_validate(raster_rgb)[0]

    # not tiled, no overview
    assert not cog_validate(raster_big, quiet=True)[0]

    # external overview
    assert not cog_validate(raster_external)[0]

    # non-sorted overview
    assert not cog_validate(raster_ovrsorted)[0]

    # invalid decimation
    assert not cog_validate(raster_decim)[0]

    # no overview
    assert cog_validate(raster_no_ovr)[0]
    assert not cog_validate(raster_no_ovr, strict=True)[0]

    with pytest.raises(Exception):
        cog_validate(raster_jpeg)

    # COG created with GDAL 3.1
    assert cog_validate(raster_rioCOGgdal31)[0]
    assert cog_validate(raster_COGgdal31)[0]


def test_cog_validate_return():
    valid, err, warn = cog_validate(raster_rgb)
    assert valid
    assert not err
    assert not warn

    valid, err, warn = cog_validate(raster_no_ovr)
    assert valid
    assert len(warn) == 1
    assert not err


def test_cog_validate_validCreatioValid(monkeypatch):
    """Should work as expected (validate cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_rgb, "cogeo.tif", jpeg_profile, quiet=True)
        assert cog_validate("cogeo.tif")

        cog_translate(
            raster_rgb, "cogeo.tif", jpeg_profile, overview_level=0, quiet=True
        )
        assert cog_validate("cogeo.tif")

        # Change in rasterio 1.0.26
        # https://github.com/mapbox/rasterio/blob/master/CHANGES.txt#L43
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="1024")
        cog_translate(
            raster_big,
            "cogeo.tif",
            jpeg_profile,
            overview_level=1,
            config=config,
            quiet=True,
        )
        assert cog_validate("cogeo.tif")
