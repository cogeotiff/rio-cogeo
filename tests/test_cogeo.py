"""tests rio_cogeo.cogeo."""

import os

import numpy

import pytest

import rasterio
from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.utils import has_mask_band, has_alpha_band
from rio_cogeo.errors import LossyCompression, IncompatibleBlockRasterSize
from rio_cogeo.profiles import cog_profiles

from .conftest import requires_webp

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
raster_path_rgba = os.path.join(FIXTURES_DIR, "image_rgba.tif")
raster_path_rgb = os.path.join(FIXTURES_DIR, "image_rgb.tif")
raster_path_nan = os.path.join(FIXTURES_DIR, "image_nan.tif")
raster_path_nodata = os.path.join(FIXTURES_DIR, "image_nodata.tif")
raster_path_float = os.path.join(FIXTURES_DIR, "image_float.tif")
raster_path_missingnodata = os.path.join(FIXTURES_DIR, "image_missing_nodata.tif")
raster_path_tags = os.path.join(FIXTURES_DIR, "image_tags.tif")
raster_path_mask = os.path.join(FIXTURES_DIR, "image_rgb_mask.tif")
raster_path_small = os.path.join(FIXTURES_DIR, "image_171px.tif")
raster_path_toosmall = os.path.join(FIXTURES_DIR, "image_51px.tif")

jpeg_profile = cog_profiles.get("jpeg")
jpeg_profile.update({"blockxsize": 64, "blockysize": 64})
webp_profile = cog_profiles.get("webp")
webp_profile.update({"blockxsize": 64, "blockysize": 64})
deflate_profile = cog_profiles.get("deflate")
deflate_profile.update({"blockxsize": 64, "blockysize": 64})
raw_profile = cog_profiles.get("raw")
raw_profile.update({"blockxsize": 64, "blockysize": 64})
default_profile = cog_profiles.get("raw")


@pytest.fixture(autouse=True)
def testing_env_var(monkeypatch):
    """Set GDAL env."""
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "TRUE")
    monkeypatch.setenv("GDAL_TIFF_INTERNAL_MASK", "TRUE")
    monkeypatch.setenv("GDAL_TIFF_OVR_BLOCKSIZE", "64")


def test_cog_translate_valid(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", jpeg_profile, quiet=True)
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

        cog_translate(
            raster_path_rgb, "cogeo.tif", jpeg_profile, add_mask=True, quiet=True
        )
        with rasterio.open("cogeo.tif") as src:
            assert has_mask_band(src)
        with rasterio.open("cogeo.tif", OVERVIEW_LEVEL=1) as src:
            assert src.block_shapes[0] == (64, 64)


def test_cog_translate_NodataLossyWarning(runner):
    """Should work as expected (create cogeo file but warns no lossy compression)."""
    with runner.isolated_filesystem():
        with pytest.warns(LossyCompression):
            cog_translate(
                raster_path_rgb, "cogeo.tif", jpeg_profile, nodata=0, quiet=True
            )
            with rasterio.open("cogeo.tif") as src:
                assert src.nodata == 0
                assert src.compression.value == "JPEG"
                assert not has_mask_band(src)


def test_cog_translate_optionWarnings(runner):
    """Should work as expected but warns about invalid options."""
    with runner.isolated_filesystem():
        with pytest.warns(UserWarning):
            cog_translate(
                raster_path_rgb, "cogeo.tif", jpeg_profile, nodata=0, quiet=True
            )
            with rasterio.open("cogeo.tif") as src:
                assert src.nodata == 0
                assert src.compression.value == "JPEG"
                assert not has_mask_band(src)


def test_cog_translate_NodataMask(runner):
    """Should work as expected (create cogeo and translate nodata to mask)."""
    with runner.isolated_filesystem():
        cog_translate(
            raster_path_missingnodata,
            "cogeo.tif",
            deflate_profile,
            nodata=-9999,
            add_mask=True,
            quiet=True,
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.nodata is None
            assert has_mask_band(src)
            assert not src.dataset_mask().all()


def test_cog_translate_validRaw(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", raw_profile, quiet=True)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.is_tiled
            assert not src.compression
            assert src.interleaving.value == "PIXEL"


@requires_webp
def test_cog_translate_validAlpha(runner):
    """Should work as expected (create cogeo file with alpha band)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgba, "cogeo.tif", webp_profile, quiet=True)
        with rasterio.open("cogeo.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert src.is_tiled
            assert src.compression.value == "WEBP"
            assert has_alpha_band(src)


def test_cog_translate_valiNodataNan(runner):
    """Should work as expected and create mask from NaN."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_nan, "cogeo_nan.tif", raw_profile, quiet=True)
        with rasterio.open("cogeo_nan.tif") as src:
            assert src.meta["dtype"] == "float64"
            assert src.nodata
            assert not src.dataset_mask().all()

        cog_translate(
            raster_path_float,
            "cogeo_nan.tif",
            raw_profile,
            nodata=numpy.nan,
            quiet=True,
        )
        with rasterio.open("cogeo_nan.tif") as src:
            assert src.meta["dtype"] == "float64"
            assert src.nodata
            assert not src.dataset_mask().all()


def test_cog_translate_validOverviews(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        cog_translate(
            raster_path_rgb, "cogeo.tif", jpeg_profile, overview_level=2, quiet=True
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.overviews(1) == [2, 4]


def test_cog_translate_valiEnv(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        config = dict(GDAL_TIFF_INTERNAL_MASK=False)
        cog_translate(
            raster_path_rgba,
            "cogeo_env.tif",
            jpeg_profile,
            indexes=[1, 2, 3],
            add_mask=True,
            config=config,
            quiet=True,
        )
        with rasterio.open("cogeo_env.tif") as src:
            assert "cogeo_env.tif.msk" in src.files


def test_cog_translate_validCustom(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE=256)
        profile = jpeg_profile.copy()
        profile.update({"blockxsize": 256, "blockysize": 256})
        cog_translate(
            raster_path_rgb, "cogeo_env.tif", profile, config=config, quiet=True
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


def test_cog_translate_mask(runner):
    """Should work as expected (copy mask from input)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_mask, "cogeo.tif", jpeg_profile, quiet=True)
        with rasterio.open("cogeo.tif") as src:
            assert has_mask_band(src)


def test_cog_translate_tags(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_tags, "cogeo.tif", jpeg_profile, quiet=True)
        with rasterio.open("cogeo.tif") as src:
            assert src.tags()["OVR_RESAMPLING_ALG"] == "NEAREST"
            assert src.tags()["DatasetName"] == "my useful dataset"
            assert src.descriptions[0] == "first band"
            assert src.descriptions[1] == "second band"
            assert src.descriptions[2] == "third band"

        cog_translate(
            raster_path_tags, "cogeo.tif", raw_profile, indexes=[2], quiet=True
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.tags()["OVR_RESAMPLING_ALG"] == "NEAREST"
            assert src.tags()["DatasetName"] == "my useful dataset"
            assert src.descriptions[0] == "second band"


def test_cog_translate_valid_blocksize(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        with pytest.warns(IncompatibleBlockRasterSize):
            cog_translate(raster_path_small, "cogeo.tif", default_profile, quiet=True)
            assert cog_validate("cogeo.tif")
            with rasterio.open("cogeo.tif") as src:
                assert src.height == 171
                assert src.width == 171
                assert src.is_tiled
                assert src.profile["blockxsize"] == 128
                assert src.profile["blockysize"] == 128
                assert src.overviews(1) == [2]

        with pytest.warns(IncompatibleBlockRasterSize):
            cog_translate(
                raster_path_toosmall, "cogeo.tif", default_profile, quiet=True
            )
            assert cog_validate("cogeo.tif")
            with rasterio.open("cogeo.tif") as src:
                assert src.height == 51
                assert src.width == 51
                assert not src.is_tiled
                assert not src.profile.get("blockxsize")
                assert not src.profile.get("blockysize")
                assert not src.overviews(1)


def test_cog_translate_validDataset(runner):
    """Should work as expected (create cogeo from an open dataset)."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_rgb) as src_dst:
            cog_translate(src_dst, "cogeo.tif", jpeg_profile, quiet=True)
            assert not src_dst.closed

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
