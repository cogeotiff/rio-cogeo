"""tests rio_cogeo.cogeo."""

import os

import pytest
from click.testing import CliRunner
from rasterio.errors import NotGeoreferencedWarning

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
raster_zero_offset = os.path.join(fixture_dir, "validate", "cog_no_offest.tif")

# COG created with rio-cogeo but using gdal 3.1
raster_rioCOGgdal31 = os.path.join(fixture_dir, "validate", "image_rioCOG_gdal3.1.tif")

# COG created using GDAL COG Driver
raster_COGgdal31 = os.path.join(fixture_dir, "validate", "image_rioCOG_gdal3.1.tif")

jpeg_profile = cog_profiles.get("jpeg")
jpeg_profile.update({"blockxsize": 256, "blockysize": 256})


def test_cog_validate_valid(monkeypatch):
    """Should work as expected (validate cogeo file)."""
    config = {"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}

    # not tiled but 512x512
    assert cog_validate(raster_rgb, config=config)[0]

    # not tiled, no overview
    assert not cog_validate(raster_big, quiet=True, config=config)[0]

    # external overview
    assert not cog_validate(raster_external, config=config)[0]

    # non-sorted overview
    assert not cog_validate(raster_ovrsorted, config=config)[0]

    # invalid decimation
    assert not cog_validate(raster_decim, config=config)[0]

    # no overview
    assert cog_validate(raster_no_ovr, config=config)[0]
    assert not cog_validate(raster_no_ovr, strict=True, config=config)[0]

    assert not cog_validate(raster_jpeg, config=config)[0]

    # COG created with GDAL 3.1
    assert cog_validate(raster_rioCOGgdal31, config=config)[0]
    assert cog_validate(raster_COGgdal31, config=config)[0]

    with pytest.warns(NotGeoreferencedWarning):
        assert cog_validate(raster_zero_offset, config=config)


def test_cog_validate_return():
    """Checkout returned values."""
    valid, err, warn = cog_validate(
        raster_rgb, config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
    )
    assert valid
    assert not err
    assert not warn

    valid, err, warn = cog_validate(
        raster_no_ovr, config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
    )
    assert valid
    assert len(warn) == 1
    assert not err


def test_cog_validate_validCreatioValid(monkeypatch):
    """Should work as expected (validate cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_rgb, "cogeo.tif", jpeg_profile, quiet=True)
        assert cog_validate(
            "cogeo.tif", config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
        )

        cog_translate(
            raster_rgb, "cogeo.tif", jpeg_profile, overview_level=0, quiet=True
        )
        assert cog_validate(
            "cogeo.tif", config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
        )

        # Change in rasterio 1.0.26
        # https://github.com/mapbox/rasterio/blob/master/CHANGES.txt#L43
        config = {"GDAL_TIFF_OVR_BLOCKSIZE": "1024"}
        cog_translate(
            raster_big,
            "cogeo.tif",
            jpeg_profile,
            overview_level=1,
            config=config,
            quiet=True,
        )
        assert cog_validate(
            "cogeo.tif", config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
        )


def test_cog_validate_config(monkeypatch):
    """Should work as expected (validate cogeo file)."""
    # No external overview found
    assert cog_validate(
        raster_external, config={"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR"}
    )[0]

    # External overview found
    assert not cog_validate(
        raster_external, config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
    )[0]
    assert (
        "external"
        in cog_validate(
            raster_external, config={"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
        )[1][0]
    )
