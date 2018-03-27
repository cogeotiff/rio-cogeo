"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import sys

import click

import numpy

import rasterio
from rasterio.enums import Resampling


def cog_translate(src, dst, dst_opts,
                  indexes=None, nodata=None, alpha=None, overview_level=6, config=None):
    """
    Create Cloud Optimized Geotiff.

    Parameters
    ----------
    src : str
        input dataset path.
    dst : str
        output dataset path.
    dst_opts: dict
        cloudoptimized geotiff raster profile.
    indexes : tuple, int, optional
        Raster band indexes to copy.
    nodata, int, optional
        nodata value for mask creation.
    alpha, int, optional
        alpha band index for mask creation.
    overview_level : int, optional (default: 6)
        COGEO overview (decimation) level

    """
    config = config or {}

    with rasterio.Env(**config):
        with rasterio.open(src) as src:

            indexes = indexes if indexes else src.indexes

            meta = src.meta
            meta['count'] = len(indexes)
            meta.pop('nodata', None)
            meta.pop('alpha', None)
            meta.pop('compress', None)
            meta.update(**dst_opts)

            with rasterio.open(dst, 'w', **meta) as dst:

                mask = numpy.zeros((dst.height, dst.width), dtype=numpy.uint8)
                wind = list(dst.block_windows(1))

                with click.progressbar(wind, length=len(wind), file=sys.stderr, show_percent=True) as windows:
                    for ij, w in windows:
                        matrix = src.read(window=w, indexes=indexes, boundless=True)
                        dst.write(matrix, window=w)

                        if nodata is not None:
                            mask_value = numpy.all(matrix != nodata, axis=0).astype(numpy.uint8) * 255
                        elif alpha is not None:
                            mask_value = src.read(alpha, window=w, boundless=True)
                        else:
                            mask_value = src.dataset_mask(window=w, boundless=True)

                        mask[w.row_off:w.row_off + w.height, w.col_off:w.col_off + w.width] = mask_value

                dst.write_mask(mask)

                overviews = [2**j for j in range(1, overview_level + 1)]
                dst.build_overviews(overviews, Resampling.nearest)
                dst.update_tags(ns='rio_overview', resampling=Resampling.nearest.value)
