"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import sys
import math

import click

import numpy

import rasterio
import mercantile

from rasterio.io import MemoryFile
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
from rasterio.shutil import copy
from rasterio.transform import Affine

from supermercado.burntiles import tile_extrema

from rio_cogeo import utils


def cog_translate(
    src_path,
    dst_path,
    dst_kwargs,
    indexes=None,
    nodata=None,
    alpha=None,
    overview_level=6,
    overview_resampling="nearest",
    web_optimized=False,
    config=None,
):
    """
    Create Cloud Optimized Geotiff.

    Parameters
    ----------
    src_path : str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.
    dst_path : str or Path-like object
        An output dataset path or or PathLike object.
        Will be opened in "w" mode.
    dst_kwargs: dict
        output dataset creation options.
    indexes : tuple, int, optional
        Raster band indexes to copy.
    nodata, int, optional
        nodata value for mask creation.
    alpha, int, optional
        alpha band index for mask creation.
    overview_level : int, optional (default: 6)
        COGEO overview (decimation) level
    web_optimized: bool
         Create web-optimized cogeo.
    config : dict
        Rasterio Env options.

    """
    config = config or {}

    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:
            vrt_params = dict(add_alpha=True, resampling=Resampling.bilinear)

            indexes = indexes if indexes else src.indexes

            # TODO: What if a raster has a nodata value and an alpha band ?
            nodata = nodata if nodata is not None else src.nodata
            if nodata is not None:
                vrt_params.update(
                    dict(
                        nodata=nodata,
                        add_alpha=False,
                        src_nodata=nodata,
                        init_dest_nodata=False,
                    )
                )

            # TODO: What does this means when alpha is passed ?
            if utils.has_alpha_band(src):
                vrt_params.update(dict(add_alpha=False))

            if web_optimized:
                # TODO: add max_zoom option
                max_zoom = utils.get_max_zoom(src)
                bounds = list(
                    transform_bounds(
                        *[src.crs, "epsg:4326"] + list(src.bounds), densify_pts=21
                    )
                )

                extrema = tile_extrema(bounds, max_zoom)
                w, n = mercantile.xy(
                    *mercantile.ul(extrema["x"]["min"], extrema["y"]["min"], max_zoom)
                )

                size_power = math.log(256, 2)
                vrt_res = 40075016.686 / 2 ** (max_zoom + size_power)
                vrt_transform = Affine(vrt_res, 0, w, 0, -vrt_res, n)

                vrt_width = (extrema["x"]["max"] - extrema["x"]["min"]) * 256
                vrt_height = (extrema["y"]["max"] - extrema["y"]["min"]) * 256

                vrt_params.update(
                    dict(
                        crs="epsg:3857",
                        transform=vrt_transform,
                        width=vrt_width,
                        height=vrt_height,
                    )
                )

            with WarpedVRT(src, **vrt_params) as vrt:
                meta = vrt.meta
                meta["count"] = len(indexes)
                meta.pop("nodata", None)
                meta.pop("alpha", None)

                meta.update(**dst_kwargs)
                meta.pop("compress", None)
                meta.pop("photometric", None)

                with MemoryFile() as memfile:
                    with memfile.open(**meta) as mem:
                        wind = list(mem.block_windows(1))
                        with click.progressbar(
                            wind, length=len(wind), file=sys.stderr, show_percent=True
                        ) as windows:
                            for ij, w in windows:
                                matrix = vrt.read(window=w, indexes=indexes)
                                mem.write(matrix, window=w)

                                if nodata is not None:
                                    mask_value = (
                                        numpy.all(matrix != nodata, axis=0).astype(
                                            numpy.uint8
                                        )
                                        * 255
                                    )
                                elif alpha is not None:
                                    mask_value = vrt.read(alpha, window=w)
                                else:
                                    mask_value = vrt.dataset_mask(window=w)
                                mem.write_mask(mask_value, window=w)

                        overviews = [2 ** j for j in range(1, overview_level + 1)]

                        mem.build_overviews(overviews, Resampling[overview_resampling])
                        mem.update_tags(
                            OVR_RESAMPLING_ALG=Resampling[
                                overview_resampling
                            ].name.upper()
                        )

                        copy(mem, dst_path, copy_src_overviews=True, **dst_kwargs)
