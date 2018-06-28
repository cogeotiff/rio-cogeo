"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import sys

import click

import numpy

import rasterio
from rasterio.io import MemoryFile
from rasterio.enums import Resampling
from rasterio.shutil import copy


def cog_translate(
    src_path,
    dst_path,
    dst_kwargs,
    indexes=None,
    nodata=None,
    alpha=None,
    overview_level=6,
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
    config : dict
        Rasterio Env options.

    """
    config = config or {}

    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:

            indexes = indexes if indexes else src.indexes
            meta = src.meta
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
                            matrix = src.read(window=w, indexes=indexes)
                            mem.write(matrix, window=w)

                            if nodata is not None:
                                mask_value = (
                                    numpy.all(matrix != nodata, axis=0).astype(
                                        numpy.uint8
                                    )
                                    * 255
                                )
                            elif alpha is not None:
                                mask_value = src.read(alpha, window=w)
                            else:
                                mask_value = src.dataset_mask(window=w)

                            mask[
                                w.row_off : w.row_off + w.height,
                                w.col_off : w.col_off + w.width,
                            ] = mask_value

                    mem.write_mask(mask)

                    overviews = [2 ** j for j in range(1, overview_level + 1)]
                    mem.build_overviews(overviews, Resampling.nearest)
                    mem.update_tags(
                        ns="rio_overview", resampling=Resampling.nearest.value
                    )

                    copy(mem, dst_path, copy_src_overviews=True, **dst_kwargs)
