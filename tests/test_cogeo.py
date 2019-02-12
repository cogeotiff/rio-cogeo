"""tests rio_cogeo.cogeo."""

import os

import numpy

from click.testing import CliRunner

import rasterio
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

raster_path_rgba = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgba.tif")
raster_path_rgb = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgb.tif")
raster_path_nan = os.path.join(os.path.dirname(__file__), "fixtures", "image_nan.tif")
ycbcr_profile = cog_profiles.get("ycbcr")


def test_cog_translate_valid():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", ycbcr_profile)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert (
                not src.is_tiled
            )  # Because blocksize is 512 and the file is 512, the output is not tiled
            assert src.compression.value == "JPEG"
            assert src.photometric.value == "YCbCr"
            assert src.interleaving.value == "PIXEL"
            assert not src.overviews(1)
            assert src.tags()["OVR_RESAMPLING_ALG"] == "NEAREST"


def test_cog_translate_validRaw():
    """Should work as expected (create cogeo file)."""
    raw_profile = cog_profiles.get("raw")
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", raw_profile)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert (
                not src.is_tiled
            )  # Because blocksize is 512 and the file is 512, the output is not tiled
            assert not src.compression
            assert src.interleaving.value == "PIXEL"
            assert not src.overviews(1)


def test_cog_translate_validAlpha():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(
            raster_path_rgba,
            "cogeo_alpha.tif",
            ycbcr_profile,
            indexes=[1, 2, 3],
            alpha=4,
        )


def test_cog_translate_valiNodata():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(
            raster_path_rgba,
            "cogeo_nodata.tif",
            ycbcr_profile,
            indexes=[1, 2, 3],
            nodata=0,
        )


def test_cog_translate_valiNodataNan():
    """Should work as expected and create mask from NaN."""
    runner = CliRunner()
    profile = cog_profiles.get("deflate")
    profile.update({"blockxsize": 64, "blockysize": 64})
    with runner.isolated_filesystem():
        cog_translate(raster_path_nan, "cogeo_nan.tif", profile, nodata=numpy.nan)
        with rasterio.open("cogeo_nan.tif") as src:
            assert src.meta["dtype"] == "float64"
            assert src.is_tiled
            assert src.compression.value == "DEFLATE"
            assert src.profile["blockxsize"] == 64
            assert src.profile["blockysize"] == 64
            assert src.overviews(1) == [2, 4, 8]
            assert not src.dataset_mask().all()


def test_cog_translate_validOverviews():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", ycbcr_profile, overview_level=2)
        with rasterio.open("cogeo.tif") as src:
            assert src.overviews(1) == [2, 4]


def test_cog_translate_valiEnv():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        config = dict(GDAL_TIFF_INTERNAL_MASK=True)
        cog_translate(
            raster_path_rgba,
            "cogeo_env.tif",
            ycbcr_profile,
            indexes=[1, 2, 3],
            config=config,
        )


def test_cog_translate_validCustom():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE=256)
        ycbcr_profile.update({"blockxsize": 256, "blockysize": 256})
        cog_translate(
            raster_path_rgba,
            "cogeo_env.tif",
            ycbcr_profile,
            indexes=[1, 2, 3],
            config=config,
        )

        with rasterio.open("cogeo_env.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert src.is_tiled
            assert src.compression.value == "JPEG"
            assert src.profile["blockxsize"] == 256
            assert src.profile["blockysize"] == 256
            assert src.photometric.value == "YCbCr"
            assert src.interleaving.value == "PIXEL"
            assert src.overviews(1) == [2]
