"""create cog"""

import os
import sys

import click

import numpy

import rasterio
from rasterio.enums import Resampling
from rio_cogeo.profiles import CogeoProfiles


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', required=True, type=click.Path())
@click.option('--bidx', '-b', type=str, default='1,2,3')
@click.option('--profile', '-p', type=str, default='ycbcr')
@click.option('--nodata', type=int)
@click.option('--alpha', type=int)
@click.option('--level', type=int, default=6, help='Overview level (default: 6)')
def cogeo(path, output, bidx, profile, nodata, alpha, level):
    """Create Cloud Optimized Geotiff
    """

    bands = [int(b) for b in bidx.split(',')]
    if len(bands) != 3:
        click.Exception('invalid bdix format')

    meta_update = CogeoProfiles.get(profile)

    output = os.path.join(os.getcwd(), output)
    if os.path.exists(output):
        os.remove(output)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True, GDAL_TIFF_OVR_BLOCKSIZE=512, NUM_THREADS=8):
        with rasterio.open(path) as src:
            nodata = src.nodata if src.nodata else nodata

            meta = src.meta
            meta.update(**meta_update)
            meta['count'] = len(bands)

            with rasterio.open(output, 'w', **meta) as dst:
                mask = numpy.zeros((meta['height'], meta['width']), dtype=numpy.uint8)
                wind = list(dst.block_windows(1))
                with click.progressbar(wind, length=len(wind), file=sys.stderr, show_percent=True) as windows:
                    for ij, w in windows:
                        matrix = src.read(window=w, indexes=bands, resampling=Resampling.bilinear)
                        dst.write(matrix, window=w, indexes=bands)

                        if nodata is not None:
                            mask_value = numpy.all(matrix != nodata, axis=0).astype(numpy.uint8) * 255
                        elif alpha is not None:
                            mask_value = src.read(alpha, window=w, boundless=True,
                                                  resampling=Resampling.bilinear)
                        else:
                            mask_value = src.read_masks(1, window=w, boundless=True,
                                                        resampling=Resampling.bilinear)

                        mask[w.row_off:w.row_off + w.height, w.col_off:w.col_off + w.width] = mask_value

                dst.write_mask(mask)

                overviews = [2**j for j in range(1, level + 1)]
                dst.build_overviews(overviews, Resampling.nearest)
                dst.update_tags(ns='rio_overview', resampling=Resampling.nearest.value)
