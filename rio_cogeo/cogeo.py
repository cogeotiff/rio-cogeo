"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import sys
import math

import click
import numpy

import rasterio
import mercantile

from rasterio.io import MemoryFile
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.shutil import copy
from rasterio.warp import transform_bounds
from rasterio.transform import from_bounds

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
    config=None,
    web_optimized=False,
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
    config : dict
        Rasterio Env options.
    web_optimized: bool
        Create web-optimized cogeo.

    """
    config = config or {}

    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:
            vrt_params = dict(add_alpha=True, resampling=Resampling.bilinear)

            indexes = indexes if indexes else src.indexes
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

            if utils.has_alpha_band(src):
                vrt_params.update(dict(add_alpha=False))

            if web_optimized:
                max_zoom = utils.get_max_zoom(src)
                bounds = list(
                    transform_bounds(
                        *[src.crs, "epsg:4326"] + list(src.bounds), densify_pts=0
                    )
                )

                extrema = tile_extrema(bounds, max_zoom)
                w, n = mercantile.xy(
                    *mercantile.ul(extrema["x"]["min"], extrema["y"]["min"], max_zoom)
                )
                e, s = mercantile.xy(
                    *mercantile.ul(extrema["x"]["max"], extrema["y"]["max"], max_zoom)
                )

                dst_res = 40075000 / 2 ** (max_zoom + 8)
                vrt_width = math.ceil((e - w) / dst_res)
                vrt_height = math.ceil((s - n) / -dst_res)

                vrt_transform = from_bounds(w, s, e, n, vrt_width, vrt_height)

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
                meta.pop("compress", None)
                meta.pop("photometric", None)
                meta.update(**dst_kwargs)

                with MemoryFile() as memfile:
                    with memfile.open(**meta) as mem:
                        mask = numpy.zeros((mem.height, mem.width), dtype=numpy.uint8)
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

                                mask[
                                    w.row_off : w.row_off + w.height,
                                    w.col_off : w.col_off + w.width,
                                ] = mask_value

                        mem.write_mask(mask)
                        del mask

                        overviews = [2 ** j for j in range(1, overview_level + 1)]
                        mem.build_overviews(overviews, Resampling.nearest)
                        mem.update_tags(
                            ns="rio_overview", resampling=Resampling.nearest.value
                        )

                        copy(mem, dst_path, copy_src_overviews=True, **dst_kwargs)
