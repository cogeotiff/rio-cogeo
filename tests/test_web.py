"""tests rio_cogeo web."""

import os
import sys
import struct

import pytest
from click.testing import CliRunner

import numpy

import mercantile

import rasterio
from rasterio.warp import transform_bounds

from rio_cogeo.utils import get_max_zoom
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from rio_tiler import reader as COGreader


raster_path_web = os.path.join(os.path.dirname(__file__), "fixtures", "image_web.tif")
raster_path_north = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_north.tif"
)


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
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="128")

        cog_translate(
            raster_path_north,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
        )
        with rasterio.open("cogeo.tif") as out_dst:
            assert get_max_zoom(out_dst) == 8

        cog_translate(
            raster_path_north,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            latitude_adjustment=False,
            config=config,
        )
        with rasterio.open("cogeo.tif") as out_dst:
            assert get_max_zoom(out_dst) == 10


def test_cog_translate_web():
    """
    Test Web-Optimized COG.

    - Test COG size is a multiple of 256 (mercator tile size)
    - Test COG bounds are aligned with mercator grid at max zoom
    """
    runner = CliRunner()
    with runner.isolated_filesystem():

        web_profile = cog_profiles.get("raw")
        web_profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="128")

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
        )
        with rasterio.open(raster_path_web) as src_dst:
            with rasterio.open("cogeo.tif") as out_dst:
                blocks = list(set(out_dst.block_shapes))
                assert len(blocks) == 1
                ts = blocks[0][0]
                assert not out_dst.width % ts
                assert not out_dst.height % ts
                max_zoom = get_max_zoom(out_dst)

                bounds = list(
                    transform_bounds(
                        src_dst.crs, "epsg:4326", *src_dst.bounds, densify_pts=21
                    )
                )
                ulTile = mercantile.xy_bounds(
                    mercantile.tile(bounds[0], bounds[3], max_zoom)
                )
                assert out_dst.bounds.left == ulTile.left
                assert out_dst.bounds.top == ulTile.top

                lrTile = mercantile.xy_bounds(
                    mercantile.tile(bounds[2], bounds[1], max_zoom)
                )
                assert out_dst.bounds.right == lrTile.right
                assert round(out_dst.bounds.bottom, 6) == round(lrTile.bottom, 6)


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
    from cogdumper.cog_tiles import COGTiff
    from cogdumper.filedumper import Reader as FileReader

    runner = CliRunner()
    with runner.isolated_filesystem():

        web_profile = cog_profiles.get("raw")
        web_profile.update({"blockxsize": 256, "blockysize": 256})
        config = dict(GDAL_TIFF_OVR_BLOCKSIZE="128")

        cog_translate(
            raster_path_web,
            "cogeo.tif",
            web_profile,
            quiet=True,
            web_optimized=True,
            config=config,
        )
        with rasterio.open(raster_path_web) as src_dst:
            with rasterio.open("cogeo.tif") as out_dst:
                blocks = list(set(out_dst.block_shapes))
                assert len(blocks) == 1
                ts = blocks[0][0]
                assert not out_dst.width % ts
                assert not out_dst.height % ts
                max_zoom = get_max_zoom(out_dst)

                bounds = list(
                    transform_bounds(
                        src_dst.crs, "epsg:4326", *src_dst.bounds, densify_pts=21
                    )
                )

                minimumTile = mercantile.tile(bounds[0], bounds[3], max_zoom)
                maximumTile = mercantile.tile(bounds[2], bounds[1], max_zoom)

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

                    with rasterio.open("cogeo.tif") as src_dst:
                        data, _ = COGreader.tile(
                            src_dst, *minimumTile, resampling_method="nearest"
                        )
                    numpy.testing.assert_array_equal(data, arr)

                    # Bottom right tile
                    _, tile = cog.get_tile(4, 3, 0)
                    tile_length = 256 * 256 * 3
                    t = struct.unpack_from("{}b".format(tile_length), tile)
                    arr = numpy.array(t).reshape(256, 256, 3).astype(numpy.uint8)
                    arr = numpy.transpose(arr, [2, 0, 1])

                    with rasterio.open("cogeo.tif") as src_dst:
                        data, _ = COGreader.tile(
                            src_dst, *maximumTile, resampling_method="nearest"
                        )
                    numpy.testing.assert_array_equal(data, arr)

                    # Low resolution (overview 1)
                    # Top Left tile
                    # NOTE: overview internal tile size is 128px
                    # We need to stack two internal tiles to compare with
                    # the 256px mercator tile fetched by rio-tiler
                    # ref: https://github.com/cogeotiff/rio-cogeo/issues/60
                    _, tile = cog.get_tile(1, 0, 1)
                    tile_length = 128 * 128 * 3
                    t = struct.unpack_from("{}b".format(tile_length), tile)
                    arr1 = numpy.array(t).reshape(128, 128, 3).astype(numpy.uint8)
                    arr1 = numpy.transpose(arr1, [2, 0, 1])

                    _, tile = cog.get_tile(2, 0, 1)
                    tile_length = 128 * 128 * 3
                    t = struct.unpack_from("{}b".format(tile_length), tile)
                    arr2 = numpy.array(t).reshape(128, 128, 3).astype(numpy.uint8)
                    arr2 = numpy.transpose(arr2, [2, 0, 1])
                    arr = numpy.dstack((arr1, arr2))

                    with rasterio.open("cogeo.tif") as src_dst:
                        data, _ = COGreader.tile(
                            src_dst, 118594, 60034, 17, resampling_method="nearest"
                        )

                    data = data[:, 128:, :]
                    numpy.testing.assert_array_equal(data, arr)
