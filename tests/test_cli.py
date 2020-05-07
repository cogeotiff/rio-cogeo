"""tests rio_cogeo.cogeo."""

import os

import pytest
import rasterio

from rio_cogeo.errors import LossyCompression
from rio_cogeo.scripts.cli import cogeo
from rio_cogeo.utils import has_mask_band

raster_path_rgb = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgb.tif")
raster_path_rgba = os.path.join(os.path.dirname(__file__), "fixtures", "image_rgba.tif")
raster_path_nan = os.path.join(os.path.dirname(__file__), "fixtures", "image_nan.tif")
raster_path_nodata = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_nodata.tif"
)
raster_path_missingnodata = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_missing_nodata.tif"
)
raster_invalid_cog = os.path.join(
    os.path.dirname(__file__), "fixtures", "validate", "image_dec.tif"
)


@pytest.fixture(autouse=True)
def testing_env_var(monkeypatch):
    """Set GDAL env."""
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "TRUE")
    monkeypatch.setenv("GDAL_TIFF_INTERNAL_MASK", "TRUE")
    monkeypatch.delenv("GDAL_TIFF_OVR_BLOCKSIZE", raising=False)


def test_cogeo_valid(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--add-mask", "--quiet"]
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta["dtype"] == "uint8"
            assert src.is_tiled
            assert src.compression.value == "DEFLATE"
            assert not src.photometric
            assert src.interleaving.value == "PIXEL"
            assert not src.overviews(1)
            assert has_mask_band(src)


def test_cogeo_valid_external_mask(monkeypatch, runner):
    """Should work as expected."""
    monkeypatch.setenv("GDAL_TIFF_INTERNAL_MASK", "FALSE")
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "TRUE")

    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--add-mask"]
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert has_mask_band(src)
            assert "output.tif.msk" in src.files


def test_cogeo_validbidx(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "-b",
                "1",
                "-p",
                "raw",
                "--add-mask",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert has_mask_band(src)
            assert src.count == 1


def test_cogeo_invalidbidx(runner):
    """Should exit with invalid band indexes."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "-b", "0"]
        )
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_invalidbidxString(runner):
    """Should exit with invalid band indexes."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "-b", "a"]
        )
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_invalidThread(runner):
    """Should exit with invalid thread parameters."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--threads", "all"]
        )
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_validnodata(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        with pytest.warns(LossyCompression):
            result = runner.invoke(
                cogeo,
                [
                    "create",
                    raster_path_rgb,
                    "output.tif",
                    "--nodata",
                    "0",
                    "--cog-profile",
                    "jpeg",
                ],
            )
            assert not result.exception
            assert result.exit_code == 0
            with rasterio.open("output.tif") as src:
                assert src.nodata == 0
                assert not has_mask_band(src)

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_nodata,
                "output.tif",
                "--co",
                "BLOCKXSIZE=64",
                "--co",
                "BLOCKYSIZE=64",
                "--cog-profile",
                "deflate",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.nodata == -9999
            assert not has_mask_band(src)


def test_cogeo_validGdalOptions(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "-p",
                "raw",
                "--co",
                "COMPRESS=DEFLATE",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.compression.value == "DEFLATE"


def test_cogeo_validOvrOption(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--overview-level",
                2,
                "--overview-resampling",
                "bilinear",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.is_tiled
            assert src.overviews(1) == [2, 4]


def test_cogeo_overviewTilesize(monkeypatch, runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--quiet",
                "--co",
                "BLOCKXSIZE=128",
                "--co",
                "BLOCKYSIZE=128",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.is_tiled
            assert src.overviews(1)

        with rasterio.open("output.tif", OVERVIEW_LEVEL=1) as src:
            assert src.block_shapes[0] == (128, 128)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--quiet",
                "--co",
                "BLOCKXSIZE=128",
                "--co",
                "BLOCKYSIZE=128",
                "--overview-blocksize",
                "64",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif", OVERVIEW_LEVEL=1) as src:
            assert src.block_shapes[0] == (64, 64)

    monkeypatch.setenv("GDAL_TIFF_OVR_BLOCKSIZE", "64")
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--quiet",
                "--co",
                "BLOCKXSIZE=128",
                "--co",
                "BLOCKYSIZE=128",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif", OVERVIEW_LEVEL=1) as src:
            assert src.block_shapes[0] == (64, 64)


def test_cogeo_web(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        with pytest.warns(UserWarning):
            result = runner.invoke(
                cogeo,
                ["create", raster_path_rgb, "output.tif", "--latitude-adjustment"],
            )
            assert not result.exception
            assert result.exit_code == 0

        with pytest.warns(UserWarning):
            result = runner.invoke(
                cogeo, ["create", raster_path_rgb, "output.tif", "--global-maxzoom"]
            )
            assert not result.exception
            assert result.exit_code == 0

        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--web-optimized"]
        )
        assert not result.exception
        assert result.exit_code == 0


def test_cogeo_validgdalBlockOption(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--co",
                "BLOCKXSIZE=128",
                "--co",
                "BLOCKYSIZE=128",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.is_tiled
            assert src.overviews(1) == [2, 4]


def test_cogeo_validNodataCustom(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_nan,
                "output.tif",
                "--cog-profile",
                "deflate",
                "--nodata",
                "nan",
                "--co",
                "BLOCKXSIZE=64",
                "--co",
                "BLOCKYSIZE=64",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.meta["dtype"] == "float64"
            assert src.nodata
            assert src.compression.value == "DEFLATE"
            assert not src.dataset_mask().all()
            assert src.dataset_mask()[0][0] == 0

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_missingnodata,
                "output.tif",
                "--cog-profile",
                "deflate",
                "--nodata",
                "-9999",
                "--co",
                "BLOCKXSIZE=64",
                "--co",
                "BLOCKYSIZE=64",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.nodata == -9999
            assert src.compression.value == "DEFLATE"
            assert not src.dataset_mask().all()
            assert src.dataset_mask()[0][0] == 0
            assert src.dataset_mask()[-1][-1] == 255

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_missingnodata,
                "output.tif",
                "--cog-profile",
                "deflate",
                "--nodata",
                "none",
                "--co",
                "BLOCKXSIZE=64",
                "--co",
                "BLOCKYSIZE=64",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.compression.value == "DEFLATE"
            assert src.dataset_mask().all()

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_nan,
                "output.tif",
                "--cog-profile",
                "deflate",
                "--nodata",
                "non",
            ],
        )
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_validTempFile(monkeypatch, runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--no-in-memory"]
        )
        assert not result.exception
        assert result.exit_code == 0

    monkeypatch.setenv("IN_MEMORY_THRESHOLD", "100")
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, ["create", raster_path_rgb, "output.tif"])
        assert not result.exception
        assert result.exit_code == 0


def test_cogeo_validCompress(monkeypatch, runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--allow-intermediate-compression",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0


def test_cogeo_validate(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--quiet"]
        )
        result = runner.invoke(cogeo, ["validate", "output.tif"])
        assert "is a valid cloud optimized GeoTIFF" in result.output
        assert not result.exception
        assert result.exit_code == 0

        result = runner.invoke(cogeo, ["validate", raster_invalid_cog])
        assert "is NOT a valid cloud optimized GeoTIFF" in result.output
        assert not result.exception
        assert result.exit_code == 0


def test_cogeo_validUpercaseProfile(monkeypatch, runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            ["create", raster_path_rgb, "output.tif", "--cog-profile", "DEFLATE"],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert src.compression.value == "DEFLATE"
