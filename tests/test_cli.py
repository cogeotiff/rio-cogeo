"""tests rio_cogeo.cogeo."""

import os

import morecantile
import pytest
import rasterio

from rio_cogeo.scripts.cli import cogeo
from rio_cogeo.utils import get_zooms, has_mask_band

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
raster_path_gcps = os.path.join(os.path.dirname(__file__), "fixtures", "slc.tif")
raster_band_tags = os.path.join(
    os.path.dirname(__file__), "fixtures", "cog_band_tags.tif"
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
            assert all([(512, 512) == (h, w) for (h, w) in src.block_shapes])
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
        with pytest.warns(UserWarning):
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
                assert not src.nodata
                assert has_mask_band(src)

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
            assert all([(512, 512) == (h, w) for (h, w) in src.block_shapes])
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
            assert all([(128, 128) == (h, w) for (h, w) in src.block_shapes])
            assert src.overviews(1)

        with rasterio.open("output.tif", OVERVIEW_LEVEL=1) as src:
            assert src.block_shapes[0] == (128, 128)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            ["create", raster_path_rgb, "output.tif", "--quiet", "--blocksize", "128"],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            assert all([(128, 128) == (h, w) for (h, w) in src.block_shapes])
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
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "--web-optimized"]
        )
        assert not result.exception
        assert result.exit_code == 0

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--web-optimized",
                "--zoom-level-strategy",
                "lower",
            ],
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
            assert all([(128, 128) == (h, w) for (h, w) in src.block_shapes])
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


def test_cogeo_invalidresampling(runner):
    """Should exit with invalid resampling."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo, ["create", raster_path_rgb, "output.tif", "-r", "gauss", "-w"]
        )
        assert result.exception
        assert result.exit_code == 2

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--overview-resampling",
                "max",
                "-w",
            ],
        )
        assert result.exception
        assert result.exit_code == 2


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


@pytest.mark.parametrize(
    "src_path",
    [
        raster_path_rgb,
        raster_invalid_cog,
        raster_band_tags,
        raster_path_gcps,
    ],
)
def test_cogeo_info(src_path, runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, ["info", src_path])
        assert not result.exception
        assert result.exit_code == 0

        result = runner.invoke(cogeo, ["info", src_path, "--json"])
        assert not result.exception
        assert result.exit_code == 0


def test_cogeo_zoom_level(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--web-optimized",
                "--zoom-level",
                "18",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            _, max_zoom = get_zooms(src)
            assert max_zoom == 18

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--web-optimized",
                "--zoom-level",
                "19",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            _, max_zoom = get_zooms(src)
            assert max_zoom == 19


def test_create_web_tms(runner):
    """Should work as expected."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--web-optimized",
                "--aligned-levels",
                2,
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            meta = src.profile

        with rasterio.open("output.tif", OVERVIEW_LEVEL=0) as src:
            meta_ovr = src.profile
            assert meta_ovr["blockysize"] == meta["blockysize"]

        with open("webmercator.json", "w") as f:
            tms = morecantile.tms.get("WebMercatorQuad")
            f.write(tms.model_dump_json())

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--aligned-levels",
                "2",
                "--tms",
                "webmercator.json",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            meta_tms = src.profile

        assert meta_tms["crs"] == meta["crs"]
        assert meta_tms["transform"] == meta["transform"]
        assert meta_tms["blockysize"] == meta["blockysize"] == 256
        assert meta_tms["width"] == meta["width"]
        assert meta_tms["height"] == meta["height"]

        with rasterio.open("output.tif", OVERVIEW_LEVEL=0) as src:
            meta_ovr = src.profile
            assert meta_ovr["blockysize"] == meta_tms["blockysize"] == 256

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--aligned-levels",
                "2",
                "--blocksize",
                512,
                "--tms",
                "webmercator.json",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open("output.tif") as src:
            meta_tms = src.profile

        with rasterio.open("output.tif", OVERVIEW_LEVEL=0) as src:
            meta_ovr = src.profile
            assert meta_ovr["blockysize"] == meta_tms["blockysize"] == 512

        result = runner.invoke(
            cogeo,
            [
                "create",
                raster_path_rgb,
                "output.tif",
                "--aligned-levels",
                "2",
                "--blocksize",
                512,
                "--overview-blocksize",
                128,
                "--tms",
                "webmercator.json",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0

        with rasterio.open("output.tif", OVERVIEW_LEVEL=0) as src:
            meta_ovr = src.profile
            assert meta_ovr["blockysize"] == 128
