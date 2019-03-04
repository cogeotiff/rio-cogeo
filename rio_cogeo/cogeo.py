"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import os
import sys
import warnings

import click

import rasterio
from rasterio.io import MemoryFile
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.shutil import copy

from rio_cogeo.errors import LossyCompression
from rio_cogeo.utils import get_maximum_overview_level, has_alpha_band, has_mask_band


def cog_translate(
    src_path,
    dst_path,
    dst_kwargs,
    indexes=None,
    nodata=None,
    add_mask=None,
    overview_level=None,
    overview_resampling="nearest",
    config=None,
    quiet=False,
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
        Overwrite nodata masking values for input dataset.
    add_mask, bool, optional
        Force output dataset creation with a mask.
    overview_level : int, optional (default: 6)
        COGEO overview (decimation) level
    overview_resampling : str, optional (default: "nearest")
        Resampling algorithm for overviews
    config : dict
        Rasterio Env options.
    quiet: bool, optional (default: False)
        Mask processing steps.

    """
    config = config or {}

    if overview_level is None:
        overview_level = get_maximum_overview_level(
            src_path, min(int(dst_kwargs["blockxsize"]), int(dst_kwargs["blockysize"]))
        )

    with rasterio.Env(**config):
        with rasterio.open(src_path) as src_dst:
            meta = src_dst.meta
            indexes = indexes if indexes else src_dst.indexes
            nodata = nodata if nodata is not None else src_dst.nodata
            alpha = has_alpha_band(src_dst)
            mask = has_mask_band(src_dst)

            if not add_mask and (
                (nodata is not None or alpha)
                and dst_kwargs.get("compress") in ["JPEG", "jpeg"]
            ):
                warnings.warn(
                    "Using lossy compression with Nodata or Alpha band "
                    "can results in unwanted artefacts.",
                    LossyCompression,
                )

            vrt_params = dict(add_alpha=True)

            if nodata is not None:
                vrt_params.update(
                    dict(nodata=nodata, add_alpha=False, src_nodata=nodata)
                )

            if alpha:
                vrt_params.update(dict(add_alpha=False))

            with WarpedVRT(src_dst, **vrt_params) as vrt_dst:
                meta = vrt_dst.meta
                meta["count"] = len(indexes)

                if add_mask:
                    meta.pop("nodata", None)
                    meta.pop("alpha", None)

                meta.update(**dst_kwargs)
                meta.pop("compress", None)
                meta.pop("photometric", None)

                with MemoryFile() as memfile:
                    with memfile.open(**meta) as mem:
                        wind = list(mem.block_windows(1))

                        if not quiet:
                            click.echo("Reading input: {}".format(src_path), err=True)
                        fout = os.devnull if quiet else sys.stderr
                        with click.progressbar(
                            wind, length=len(wind), file=fout, show_percent=True
                        ) as windows:
                            for ij, w in windows:
                                matrix = vrt_dst.read(window=w, indexes=indexes)
                                mem.write(matrix, window=w)

                                if add_mask or mask:
                                    mask_value = vrt_dst.dataset_mask(window=w)
                                    mem.write_mask(mask_value, window=w)

                        if not quiet:
                            click.echo("Adding overviews...", err=True)
                        overviews = [2 ** j for j in range(1, overview_level + 1)]
                        mem.build_overviews(overviews, Resampling[overview_resampling])

                        if not quiet:
                            click.echo("Updating dataset tags...", err=True)

                        for i, b in enumerate(indexes):
                            mem.set_band_description(i + 1, src_dst.descriptions[b - 1])

                        tags = src_dst.tags()
                        tags.update(
                            dict(
                                OVR_RESAMPLING_ALG=Resampling[
                                    overview_resampling
                                ].name.upper()
                            )
                        )
                        mem.update_tags(**tags)

                        if not quiet:
                            click.echo(
                                "Writing output to: {}".format(dst_path), err=True
                            )
                        copy(mem, dst_path, copy_src_overviews=True, **dst_kwargs)
