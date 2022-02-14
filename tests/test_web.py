"""tests rio_cogeo web."""

import os
import struct
import sys

import morecantile
import numpy
import pytest
import rasterio
from click.testing import CliRunner
from cogdumper.cog_tiles import COGTiff
from cogdumper.filedumper import Reader as FileReader
from rasterio.warp import transform_bounds
from rio_tiler.io import COGReader

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rio_cogeo.utils import get_zooms

raster_path_web = os.path.join(os.path.dirname(__file__), "fixtures", "image_web.tif")
raster_path_north = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_north.tif"
)
raster_geos = os.path.join(os.path.dirname(__file__), "fixtures", "image_geos.tif")


def test_cog_translate_webZooms():
    """
    Test Web-Optimized COG.

    - Test COG size is a multiple of 256 (mercator tile size)
    - Test COG bounds are aligned with mercator grid at max zoom
    - Test high resolution internal tiles are equal to mercator tile using
      cogdumper and rio-tiler
    - Test overview internal tiles are equal to mercator tile using
      cogdumper and rio-tiler
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        web_profile = cog_profiles.get("raw")
        web_profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="256")

        cog_translate(
            raster_path_north,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
        )
        with rasterio.open("cogeo.tif") as out_dst:
            _, maxzoom = get_zooms(out_dst)
            assert maxzoom == 9

        cog_translate(
            raster_path_north,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            zoom_level_strategy="lower",
            config=config,
        )
        with rasterio.open("cogeo.tif") as out_dst:
            _, maxzoom = get_zooms(out_dst)
            assert maxzoom == 8


def test_cog_translate_web():
    """
    Test Web-Optimized COG.

    - Test COG size is a multiple of 256 (mercator tile size)
    - Test COG bounds are aligned with mercator grid at max zoom
    """
    tms = morecantile.tms.get("WebMercatorQuad")

    runner = CliRunner()
    with runner.isolated_filesystem():

        web_profile = cog_profiles.get("raw")
        web_profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="256")

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
            aligned_levels=0,
        )
        with rasterio.open(raster_path_web) as src_dst:
            with rasterio.open("cogeo.tif") as out_dst:
                blocks = list(set(out_dst.block_shapes))
                assert len(blocks) == 1
                ts = blocks[0][0]
                assert not out_dst.width % ts
                assert not out_dst.height % ts
                _, max_zoom = get_zooms(out_dst)

                bounds = list(
                    transform_bounds(
                        src_dst.crs, "epsg:4326", *src_dst.bounds, densify_pts=21
                    )
                )
                ulTile = tms.xy_bounds(tms.tile(bounds[0], bounds[3], max_zoom))
                assert out_dst.bounds.left == ulTile.left
                assert out_dst.bounds.top == ulTile.top

                lrTile = tms.xy_bounds(tms.tile(bounds[2], bounds[1], max_zoom))
                assert out_dst.bounds.right == lrTile.right
                assert round(out_dst.bounds.bottom, 6) == round(lrTile.bottom, 6)
                assert out_dst.tags(ns="TILING_SCHEME")["NAME"] == "WEBMERCATORQUAD"
                assert out_dst.tags(ns="TILING_SCHEME")["ZOOM_LEVEL"]
                assert not out_dst.tags(ns="TILING_SCHEME").get("ALIGNED_LEVELS")

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
            aligned_levels=4,
        )
        with rasterio.open("cogeo.tif") as out_dst:
            assert out_dst.tags(ns="TILING_SCHEME")["NAME"] == "WEBMERCATORQUAD"
            assert out_dst.tags(ns="TILING_SCHEME")["ZOOM_LEVEL"]
            assert out_dst.tags(ns="TILING_SCHEME")["ALIGNED_LEVELS"] == "4"


@pytest.mark.skipif(sys.version_info < (3, 6), reason="requires python3.6 or higher")
def test_cog_translate_Internal():
    """
    Test Web-Optimized COG.

    - Test COG size is a multiple of 256 (mercator tile size)
    - Test COG bounds are aligned with mercator grid at max zoom
    - Test high resolution internal tiles are equal to mercator tile using
      cogdumper and rio-tiler
    - Test overview internal tiles are equal to mercator tile using
      cogdumper and rio-tiler
    """
    tms = morecantile.tms.get("WebMercatorQuad")

    runner = CliRunner()
    with runner.isolated_filesystem():

        web_profile = cog_profiles.get("raw")
        web_profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="256")

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
            aligned_levels=0,
        )
        with rasterio.open(raster_path_web) as src_dst:
            with rasterio.open("cogeo.tif") as out_dst:
                blocks = list(set(out_dst.block_shapes))
                assert len(blocks) == 1
                ts = blocks[0][0]
                assert not out_dst.width % ts
                assert not out_dst.height % ts
                _, max_zoom = get_zooms(out_dst)

                bounds = list(
                    transform_bounds(
                        src_dst.crs, "epsg:4326", *src_dst.bounds, densify_pts=21
                    )
                )

                minimumTile = tms.tile(bounds[0], bounds[3], max_zoom)
                maximumTile = tms.tile(bounds[2], bounds[1], max_zoom)

                with open("cogeo.tif", "rb") as out_body:
                    reader = FileReader(out_body)
                    cog = COGTiff(reader.read)

                    # High resolution
                    # Top Left tile
                    _, tile = cog.get_tile(0, 0, 0)
                    tile_length = 256 * 256 * 3
                    t = struct.unpack_from("{}b".format(tile_length), tile)
                    arr = numpy.array(t).reshape(256, 256, 3).astype(numpy.uint8)
                    arr = numpy.transpose(arr, [2, 0, 1])

                    with COGReader("cogeo.tif") as src_dst:
                        data, _ = src_dst.tile(
                            *minimumTile, resampling_method="nearest"
                        )
                    numpy.testing.assert_array_equal(data, arr)

                    # Bottom right tile
                    _, tile = cog.get_tile(4, 3, 0)
                    tile_length = 256 * 256 * 3
                    t = struct.unpack_from("{}b".format(tile_length), tile)
                    arr = numpy.array(t).reshape(256, 256, 3).astype(numpy.uint8)
                    arr = numpy.transpose(arr, [2, 0, 1])

                    with COGReader("cogeo.tif") as src_dst:
                        data, _ = src_dst.tile(
                            *maximumTile, resampling_method="nearest"
                        )
                    numpy.testing.assert_array_equal(data, arr)


def test_cog_translate_web_align():
    """
    Test Web-Optimized COG.

    - Test COG bounds (thus block) is aligned with Zoom levels

    """
    tms = morecantile.tms.get("WebMercatorQuad")

    runner = CliRunner()
    with runner.isolated_filesystem():

        web_profile = cog_profiles.get("raw")
        web_profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="256")

        with rasterio.open(raster_path_web) as src_dst:
            _, max_zoom = get_zooms(src_dst)

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
            aligned_levels=2,
        )
        with COGReader(raster_path_web) as src_dst:
            bounds = src_dst.bounds
            with COGReader("cogeo.tif") as cog:
                _, max_zoom = get_zooms(cog.dataset)
                ulTile = tms.xy_bounds(tms.tile(bounds[0], bounds[3], max_zoom - 2))
                assert round(cog.dataset.bounds[0], 5) == round(ulTile.left, 5)
                assert round(cog.dataset.bounds[3], 5) == round(ulTile.top, 5)

                lrTile = tms.xy_bounds(tms.tile(bounds[2], bounds[1], max_zoom - 2))
                assert round(cog.dataset.bounds[2], 5) == round(lrTile.right, 5)
                assert round(cog.dataset.bounds[1], 5) == round(lrTile.bottom, 5)

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
            aligned_levels=3,
        )
        with COGReader(raster_path_web) as src_dst:
            bounds = src_dst.bounds
            with COGReader("cogeo.tif") as cog_dst:
                _, max_zoom = get_zooms(cog_dst.dataset)
                ulTile = tms.xy_bounds(tms.tile(bounds[0], bounds[3], max_zoom - 3))
                assert round(cog_dst.dataset.bounds[0], 5) == round(ulTile.left, 5)
                assert round(cog_dst.dataset.bounds[3], 5) == round(ulTile.top, 5)

                lrTile = tms.xy_bounds(tms.tile(bounds[2], bounds[1], max_zoom - 3))
                assert round(cog_dst.dataset.bounds[2], 5) == round(lrTile.right, 5)
                assert round(cog_dst.dataset.bounds[1], 5) == round(lrTile.bottom, 5)


def test_cog_translate_web_geos():
    """
    Test Web-Optimized COG for input GEOS dataset.

    - Test COG bounds (thus block) is aligned with Zoom levels

    """
    runner = CliRunner()
    with runner.isolated_filesystem():

        profile = cog_profiles.get("jpeg")
        profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="256", GDAL_TIFF_INTERNAL_MASK=True)

        cog_translate(
            raster_geos,
            "cogeo.tif",
            profile,
            quiet=True,
            web_optimized=True,
            config=config,
        )
        with COGReader("cogeo.tif") as cog_dst:
            assert cog_dst.dataset.shape == (512, 1024)
