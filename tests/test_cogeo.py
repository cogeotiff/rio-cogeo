"""tests rio_cogeo.cogeo."""

import os

import numpy

import pytest
from click.testing import CliRunner

import rasterio
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.utils import has_mask_band, has_alpha_band
from rio_cogeo.errors import LossyCompression
from rio_cogeo.profiles import cog_profiles

from .conftest import requires_webp


raster_path_rgba = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgba.tif")
raster_path_rgb = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgb.tif")
raster_path_nan = os.path.join(os.path.dirname(__file__), "fixtures", "image_nan.tif")
raster_path_nodata = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_nodata.tif"
)
raster_path_float = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_float.tif"
)
raster_path_missingnodata = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_missing_nodata.tif"
)


jpeg_profile = cog_profiles.get("jpeg")
jpeg_profile.update({"blockxsize": 64, "blockysize": 64})
webp_profile = cog_profiles.get("webp")
webp_profile.update({"blockxsize": 64, "blockysize": 64})
deflate_profile = cog_profiles.get("deflate")
deflate_profile.update({"blockxsize": 64, "blockysize": 64})
raw_profile = cog_profiles.get("raw")
raw_profile.update({"blockxsize": 64, "blockysize": 64})


@pytest.fixture(autouse=True)
def testing_env_var(monkeypatch):
    """Set GDAL env."""
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "TRUE")
    monkeypatch.setenv("GDAL_TIFF_INTERNAL_MASK", "TRUE")
    monkeypatch.setenv("GDAL_TIFF_OVR_BLOCKSIZE", "64")


def test_cog_translate_valid():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", jpeg_profile)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert src.is_tiled
            assert src.profile["blockxsize"] == 64
            assert src.profile["blockysize"] == 64
            assert src.compression.value == "JPEG"
            assert src.photometric.value == "YCbCr"
            assert src.interleaving.value == "PIXEL"
            assert src.overviews(1) == [2, 4, 8]
            assert src.tags()["OVR_RESAMPLING_ALG"] == "NEAREST"
            assert not has_mask_band(src)

        cog_translate(raster_path_rgb, "cogeo.tif", jpeg_profile, add_mask=True)
        with rasterio.open("cogeo.tif") as src:
            assert has_mask_band(src)


def test_cog_translate_NodataLossyWarning():
    """Should work as expected (create cogeo file but warns no lossy compression)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with pytest.warns(LossyCompression):
            cog_translate(raster_path_rgb, "cogeo.tif", jpeg_profile, nodata=0)
            with rasterio.open("cogeo.tif") as src:
                assert src.nodata == 0
                assert src.compression.value == "JPEG"
                assert not has_mask_band(src)


def test_cog_translate_NodataMask():
    """Should work as expected (create cogeo and translate nodata to mask)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(
            raster_path_missingnodata,
            "cogeo.tif",
            deflate_profile,
            nodata=-9999,
            add_mask=True,
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.nodata is None
            assert has_mask_band(src)
            assert not src.dataset_mask().all()

        cog_translate(raster_path_nodata, "cogeo.tif", deflate_profile, add_mask=True)
        with rasterio.open("cogeo.tif") as src:
            assert src.nodata is None
            assert has_mask_band(src)
            assert not src.dataset_mask().all()


def test_cog_translate_validRaw():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", raw_profile)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.is_tiled
            assert not src.compression
            assert src.interleaving.value == "PIXEL"


@requires_webp
def test_cog_translate_validAlpha():
    """Should work as expected (create cogeo file with alpha band)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgba, "cogeo.tif", webp_profile)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert src.is_tiled
            assert src.compression.value == "WEBP"
            assert has_alpha_band(src)


def test_cog_translate_valiNodataNan():
    """Should work as expected and create mask from NaN."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_nan, "cogeo_nan.tif", raw_profile)
        with rasterio.open("cogeo_nan.tif") as src:
            assert src.meta["dtype"] == "float64"
            assert src.nodata
            assert not src.dataset_mask().all()

        cog_translate(raster_path_float, "cogeo_nan.tif", raw_profile, nodata=numpy.nan)
        with rasterio.open("cogeo_nan.tif") as src:
            assert src.meta["dtype"] == "float64"
            assert src.nodata
            assert not src.dataset_mask().all()


def test_cog_translate_validOverviews():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", jpeg_profile, overview_level=2)
        with rasterio.open("cogeo.tif") as src:
            assert src.overviews(1) == [2, 4]


def test_cog_translate_valiEnv():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        config = dict(GDAL_TIFF_INTERNAL_MASK=False)
        cog_translate(
            raster_path_rgba,
            "cogeo_env.tif",
            jpeg_profile,
            indexes=[1, 2, 3],
            add_mask=True,
            config=config,
        )
        with rasterio.open("cogeo_env.tif") as src:
            assert "cogeo_env.tif.msk" in src.files


def test_cog_translate_validCustom():
    """Should work as expected (create cogeo file)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE=256)
        profile = jpeg_profile.copy()
        profile.update({"blockxsize": 256, "blockysize": 256})
        cog_translate(raster_path_rgb, "cogeo_env.tif", profile, config=config)
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
