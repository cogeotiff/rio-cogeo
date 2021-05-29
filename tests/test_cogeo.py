"""tests rio_cogeo.cogeo."""

import os
import pathlib

import numpy
import pytest
import rasterio
from rasterio.enums import ColorInterp
from rasterio.io import MemoryFile
from rasterio.shutil import copy
from rasterio.vrt import WarpedVRT

from rio_cogeo.cogeo import TemporaryRasterFile, cog_info, cog_translate, cog_validate
from rio_cogeo.errors import IncompatibleBlockRasterSize, IncompatibleOptions
from rio_cogeo.profiles import cog_profiles
from rio_cogeo.utils import has_alpha_band, has_mask_band

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
raster_path_offsets = os.path.join(FIXTURES_DIR, "image_with_offsets.tif")
raster_colormap = os.path.join(FIXTURES_DIR, "image_colormap.tif")
raster_nocolormap = os.path.join(FIXTURES_DIR, "image_nocolormap.tif")
raster_badoutputsize = os.path.join(FIXTURES_DIR, "bad_output_vrt.tif")
raster_web_z5_z11 = os.path.join(FIXTURES_DIR, "image_web_z5_z11.tif")

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


def _validate_translated_rgb_jpeg(src):
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


def test_cog_translate_valid(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", jpeg_profile, quiet=True)
        with rasterio.open("cogeo.tif") as src:
            _validate_translated_rgb_jpeg(src)

        cog_translate(
            raster_path_rgb, "cogeo.tif", jpeg_profile, add_mask=True, quiet=True
        )
        with rasterio.open("cogeo.tif") as src:
            assert has_mask_band(src)
        with rasterio.open("cogeo.tif", OVERVIEW_LEVEL=1) as src:
            assert src.block_shapes[0] == (64, 64)
        with rasterio.open(raster_path_rgb) as src:
            with rasterio.open("cogeo.tif") as dst:
                assert src.colorinterp == dst.colorinterp


def test_cog_translate_NodataLossyWarning(runner):
    """Should work as expected (create cogeo file but warns about mask creation)."""
    with runner.isolated_filesystem():
        with pytest.warns(UserWarning):
            cog_translate(
                raster_path_rgb, "cogeo.tif", jpeg_profile, nodata=0, quiet=True
            )
            with rasterio.open("cogeo.tif") as src:
                assert not src.nodata
                assert src.compression.value == "JPEG"
                assert has_mask_band(src)


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


def test_cog_translate_validIndexes(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        cog_translate(raster_path_rgb, "cogeo.tif", raw_profile, indexes=1, quiet=True)
        with rasterio.open("cogeo.tif") as src:
            assert src.count == 1

        cog_translate(
            raster_path_rgb, "cogeo.tif", raw_profile, indexes=[1], quiet=True
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.count == 1

        cog_translate(
            raster_path_rgb, "cogeo.tif", raw_profile, indexes=(1,), quiet=True
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.count == 1


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

        with rasterio.open(raster_path_rgba) as src:
            with rasterio.open("cogeo.tif") as dst:
                assert src.colorinterp == dst.colorinterp

        with pytest.warns(UserWarning):
            cog_translate(raster_path_rgba, "cogeo.tif", jpeg_profile, quiet=True)
            with rasterio.open("cogeo.tif") as src:
                assert src.count == 3

        with pytest.warns(UserWarning):
            cog_translate(
                raster_path_rgba,
                "cogeo.tif",
                jpeg_profile,
                indexes=(1, 2, 3, 4),
                quiet=True,
            )
            with rasterio.open("cogeo.tif") as src:
                assert src.count == 3
                assert src.compression.value == "JPEG"
                assert has_mask_band(src)

        with pytest.warns(UserWarning):
            cog_translate(
                raster_path_rgba, "cogeo.tif", jpeg_profile, indexes=(1,), quiet=True
            )
            with rasterio.open("cogeo.tif") as src:
                assert src.count == 1
                assert src.compression.value == "JPEG"
                assert has_mask_band(src)


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
            raster_path_tags,
            "cogeo.tif",
            jpeg_profile,
            quiet=True,
            additional_cog_metadata={"comment": "it should work"},
        )
        with rasterio.open("cogeo.tif") as src:
            assert src.tags()["OVR_RESAMPLING_ALG"] == "NEAREST"
            assert src.tags()["comment"] == "it should work"

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


def test_cog_translate_dataset(runner):
    """Should work as expected (create cogeo from an open dataset)."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_rgb) as src_dst:
            cog_translate(src_dst, "cogeo.tif", jpeg_profile, quiet=True)
            assert not src_dst.closed

        with rasterio.open("cogeo.tif") as src:
            _validate_translated_rgb_jpeg(src)


def test_cog_translate_memfile(runner):
    """Should work as expected (create cogeo from an open memfile)."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_rgb) as dataset:
            data = dataset.read()
            with MemoryFile() as memfile:
                with memfile.open(**dataset.profile) as mem:
                    mem.write(data)
                    cog_translate(mem, "cogeo.tif", jpeg_profile, quiet=True)

        with rasterio.open("cogeo.tif") as src:
            _validate_translated_rgb_jpeg(src)


def test_cog_translate_to_memfile(runner):
    """Create COG in memory and using in memory or in disk temp files."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_rgb) as dataset:
            with MemoryFile() as memfile:
                cog_translate(dataset, memfile.name, deflate_profile, quiet=True)
                with memfile.open() as src:
                    assert src.width == dataset.width

        with rasterio.open(raster_path_rgb) as dataset:
            with MemoryFile() as memfile:
                cog_translate(
                    dataset, memfile.name, deflate_profile, in_memory=False, quiet=True
                )
                with memfile.open() as src:
                    assert src.width == dataset.width


def test_cog_translate_warpedvrt(runner):
    """Should work as expected (create cogeo from an open memfile)."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_rgb) as dataset:
            with WarpedVRT(dataset) as vrt:
                cog_translate(vrt, "cogeo.tif", jpeg_profile, quiet=True)

        with rasterio.open("cogeo.tif") as src:
            _validate_translated_rgb_jpeg(src)


def test_cog_translate_forward_tags(runner):
    """Should work as expected (create cogeo from an open memfile)."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_rgb) as dataset:
            data = dataset.read()
            with MemoryFile() as memfile:
                with memfile.open(**dataset.profile) as mem:
                    mem.write(data)
                    mem.update_tags(1, jqt="dre")
                    cog_translate(
                        mem,
                        "cogeo.tif",
                        jpeg_profile,
                        forward_band_tags=True,
                        quiet=True,
                    )

        with rasterio.open("cogeo.tif") as src:
            _validate_translated_rgb_jpeg(src)
            assert src.tags(1) == {"jqt": "dre"}


def test_cog_translate_oneBandJpeg(runner):
    """Should work as expected (create cogeo file)."""
    with runner.isolated_filesystem():
        profile = jpeg_profile.copy()
        with pytest.warns(UserWarning):
            cog_translate(
                raster_path_rgb, "cogeo.tif", profile, indexes=(1,), quiet=True
            )
        with rasterio.open("cogeo.tif") as src:
            assert src.compression.value == "JPEG"
            assert src.colorinterp[0] == rasterio.enums.ColorInterp.gray


def test_cog_translate_forward_scales(runner):
    """Scales and Offset should be passed to the output file."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_path_offsets) as dataset:
            offs = dataset.offsets
            scls = dataset.scales
            cog_translate(
                dataset,
                "cogeo.tif",
                deflate_profile,
                forward_band_tags=True,
                quiet=True,
            )

        with rasterio.open("cogeo.tif") as src:
            assert src.scales == scls
            assert src.offsets == offs


def test_cog_translate_forward_cmap(runner):
    """Colormap should be passed to the output file."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_colormap) as dataset:
            cog_translate(dataset, "cogeo.tif", deflate_profile, quiet=True)

            with rasterio.open("cogeo.tif") as cog:
                assert cog.colormap(1) == dataset.colormap(1)
                assert cog.colorinterp == dataset.colorinterp

        # add an external colormap
        cmap = {0: (0, 0, 0, 0), 1: (1, 2, 3, 255)}
        with rasterio.open(raster_nocolormap) as dataset:
            cog_translate(
                dataset, "cogeo.tif", deflate_profile, quiet=True, colormap=cmap
            )
            with rasterio.open("cogeo.tif") as cog:
                assert cog.colormap(1)[1] == cmap[1]
                assert cog.colorinterp == (ColorInterp.palette,)

        with pytest.raises(IncompatibleOptions):
            with rasterio.open(raster_nocolormap) as dataset:
                cog_translate(
                    dataset,
                    "cogeo.tif",
                    deflate_profile,
                    quiet=True,
                    colormap=cmap,
                    indexes=(1, 1, 1),
                )

        # add an external colormap (warns of wrong colorinterp)
        with pytest.warns(UserWarning):
            with rasterio.open(raster_path_rgb) as dataset:
                cog_translate(
                    dataset,
                    "cogeo.tif",
                    deflate_profile,
                    quiet=True,
                    colormap=cmap,
                    indexes=(1,),
                )
                with rasterio.open("cogeo.tif") as cog:
                    assert cog.colormap(1)[1] == cmap[1]
                    assert cog.colorinterp == (ColorInterp.palette,)
                    assert not cog.colorinterp[0] == dataset.colorinterp[0]

        # Input dataset has colorinterp set to `Palette` but no colormap
        with pytest.warns(UserWarning):
            with rasterio.open(raster_nocolormap) as dataset:
                cog_translate(dataset, "cogeo.tif", deflate_profile, quiet=True)
                with rasterio.open("cogeo.tif") as cog:
                    assert cog.colorinterp == dataset.colorinterp


def test_output_size(runner):
    """Validate fix for #140."""
    with runner.isolated_filesystem():
        with rasterio.open(raster_badoutputsize) as src_dst:
            with MemoryFile() as memfile:
                cog_translate(src_dst, memfile.name, deflate_profile, quiet=True)
                with memfile.open() as dataset:
                    assert src_dst.width == dataset.width
                    assert src_dst.height == dataset.height


def test_cog_info():
    """Test COGEO info."""
    info = cog_info(raster_web_z5_z11)
    assert info.COG
    assert info.GEO.CRS == "EPSG:3857"
    assert info.GEO.MinZoom == 5
    assert info.GEO.MaxZoom == 11
    assert len(info.IFD) == 6
    assert info.Tags["Image Metadata"]
    assert info.Tags["Image Structure"]


def test_cog_info_dict_access():
    """Test dictionary access to COGEO info."""
    info = cog_info(raster_web_z5_z11)
    assert info["COG"]
    assert info["GEO"]["CRS"] == "EPSG:3857"
    assert info["GEO"]["MinZoom"] == 5
    assert info["GEO"]["MaxZoom"] == 11
    assert len(info["IFD"]) == 6
    assert info["Tags"]["Image Metadata"]
    assert info["Tags"]["Image Structure"]
    # assert info.GEO.MinZoom == 5
    # assert info.GEO.MaxZoom == 11
    # assert len(info.IFD) == 6
    # assert info.Tags["Image Metadata"]
    # assert info.Tags["Image Structure"]


@pytest.mark.parametrize(
    "fname",
    [
        "mytif.tif",
        pathlib.Path("mytif.tif"),
        "s3://abucket/adirectory/afile.tif",
        "https://ahost/adirectory/afile.tif",
    ],
)
def test_temporaryRaster(fname):
    """Test TemporaryRasterFile class with vsi and pathlib."""
    with TemporaryRasterFile(fname) as f:
        pass
    assert not os.path.exists(f.name)


@pytest.mark.parametrize(
    "src_path",
    [
        raster_path_rgba,
        raster_path_rgb,
        raster_path_nan,
        raster_path_nodata,
        raster_path_float,
    ],
)
def test_gdal_cog(src_path, runner):
    """Test GDAL COG."""
    with runner.isolated_filesystem():
        cog_translate(
            src_path,
            "cogeo.tif",
            cog_profiles.get("raw"),
            quiet=True,
            use_cog_driver=True,
        )
        assert cog_validate("cogeo.tif")


def test_gdal_cog_compare(runner):
    """Test GDAL COG."""
    with runner.isolated_filesystem():
        profile = cog_profiles.get("jpeg")
        profile["blockxsize"] = 256
        profile["blockysize"] = 256

        # rio cogeo GDAL COG
        cog_translate(
            raster_path_rgba,
            "gdalcogeo.tif",
            profile.copy(),
            quiet=True,
            use_cog_driver=True,
        )

        # pure COG
        copy(raster_path_rgba, "cog.tif", driver="COG", blocksize=256, compress="JPEG")

        # rio cogeo cog
        cog_translate(
            raster_path_rgba,
            "riocogeo.tif",
            profile.copy(),
            indexes=(1, 2, 3,),
            add_mask=True,
            quiet=True,
        )

        with rasterio.open("riocogeo.tif") as riocogeo, rasterio.open(
            "gdalcogeo.tif"
        ) as gdalcogeo, rasterio.open("cog.tif") as cog:
            assert cog.profile == gdalcogeo.profile == riocogeo.profile
            assert cog.overviews(1) == gdalcogeo.overviews(1) == riocogeo.overviews(1)


def test_gdal_cog_compareWeb(runner):
    """Test GDAL COG."""
    with runner.isolated_filesystem():
        profile = cog_profiles.get("jpeg")
        profile["blockxsize"] = 256
        profile["blockysize"] = 256

        # rio cogeo GDAL COG
        cog_translate(
            raster_path_rgba,
            "gdalcogeo.tif",
            profile.copy(),
            quiet=True,
            use_cog_driver=True,
            web_optimized=True,
        )

        # pure COG
        copy(
            raster_path_rgba,
            "cog.tif",
            driver="COG",
            blocksize=256,
            compress="JPEG",
            TILING_SCHEME="GoogleMapsCompatible",
        )

        with rasterio.open("gdalcogeo.tif") as gdalcogeo, rasterio.open(
            "cog.tif"
        ) as cog:
            assert cog.meta == gdalcogeo.meta
