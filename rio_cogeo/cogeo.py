"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import os
import sys
import warnings

import click

import rasterio
from rasterio.io import MemoryFile
from rasterio.env import GDALVersion
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

            if overview_level is None:
                overview_level = get_maximum_overview_level(
                    src_dst,
                    min(int(dst_kwargs["blockxsize"]), int(dst_kwargs["blockysize"])),
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


def cog_validate(src_path):
    """
    Validate Cloud Optimized Geotiff.

    Parameters
    ----------
    src_path : str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.

    This script is the rasterio equivalent of
    https://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/validate_cloud_optimized_geotiff.py

    """
    errors = []
    warnings = []
    details = {}

    if not GDALVersion.runtime().at_least("2.2"):
        raise Exception("GDAL 2.2 or above required")

    config = dict(GDAL_DISABLE_READDIR_ON_OPEN="FALSE")
    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:
            if not src.driver == "GTiff":
                raise Exception("The file is not a GeoTIFF")

            filelist = [os.path.basename(f) for f in src.files]
            src_bname = os.path.basename(src_path)
            if len(filelist) > 1 and src_bname + ".ovr" in filelist:
                errors.append(
                    "Overviews found in external .ovr file. They should be internal"
                )

            if src.width >= 512 or src.height >= 512:
                if not src.is_tiled:
                    errors.append(
                        "The file is greater than 512xH or 512xW, but is not tiled"
                    )

                overviews = src.overviews(1)
                if not overviews:
                    warnings.append(
                        "The file is greater than 512xH or 512xW, it is recommended "
                        "to include internal overviews"
                    )

            ifd_offset = int(src.get_tag_item("IFD_OFFSET", "TIFF", bidx=1))
            ifd_offsets = [ifd_offset]
            if ifd_offset not in (8, 16):
                errors.append(
                    "The offset of the main IFD should be 8 for ClassicTIFF "
                    "or 16 for BigTIFF. It is {} instead".format(ifd_offset)
                )

            details["ifd_offsets"] = {}
            details["ifd_offsets"]["main"] = ifd_offset

            if not overviews == sorted(overviews):
                errors.append("Overviews should be sorted")

            for ix, dec in enumerate(overviews):

                # NOTE: Size check is handled in rasterio `src.overviews` methods
                # https://github.com/mapbox/rasterio/blob/4ebdaa08cdcc65b141ed3fe95cf8bbdd9117bc0b/rasterio/_base.pyx
                # We just need to make sure the decimation level is > 1
                if not dec > 1:
                    errors.append(
                        "Invalid Decimation {} for overview level {}".format(dec, ix)
                    )

                # Check that the IFD of descending overviews are sorted by increasing
                # offsets
                ifd_offset = int(src.get_tag_item("IFD_OFFSET", "TIFF", bidx=1, ovr=ix))
                ifd_offsets.append(ifd_offset)

                details["ifd_offsets"]["overview_{}".format(ix)] = ifd_offset
                if ifd_offsets[-1] < ifd_offsets[-2]:
                    if ix == 0:
                        errors.append(
                            "The offset of the IFD for overview of index {} is {}, "
                            "whereas it should be greater than the one of the main "
                            "image, which is at byte {}".format(
                                ix, ifd_offsets[-1], ifd_offsets[-2]
                            )
                        )
                    else:
                        errors.append(
                            "The offset of the IFD for overview of index {} is {}, "
                            "whereas it should be greater than the one of index {}, "
                            "which is at byte {}".format(
                                ix, ifd_offsets[-1], ix - 1, ifd_offsets[-2]
                            )
                        )

            block_offset = int(src.get_tag_item("BLOCK_OFFSET_0_0", "TIFF", bidx=1))
            if not block_offset:
                errors.append("Missing BLOCK_OFFSET_0_0")

            data_offset = int(block_offset) if block_offset else None
            data_offsets = [data_offset]
            details["data_offsets"] = {}
            details["data_offsets"]["main"] = data_offset

            for ix, dec in enumerate(overviews):
                data_offset = int(
                    src.get_tag_item("BLOCK_OFFSET_0_0", "TIFF", bidx=1, ovr=ix)
                )
                data_offsets.append(data_offset)
                details["data_offsets"]["overview_{}".format(ix)] = data_offset

            if data_offsets[-1] < ifd_offsets[-1]:
                if len(overviews) > 0:
                    errors.append(
                        "The offset of the first block of the smallest overview "
                        "should be after its IFD"
                    )
                else:
                    errors.append(
                        "The offset of the first block of the image should "
                        "be after its IFD"
                    )

            for i in range(len(data_offsets) - 2, 0, -1):
                if data_offsets[i] < data_offsets[i + 1]:
                    errors.append(
                        "The offset of the first block of overview of index {} should "
                        "be after the one of the overview of index {}".format(i - 1, i)
                    )

            if len(data_offsets) >= 2 and data_offsets[0] < data_offsets[1]:
                errors.append(
                    "The offset of the first block of the main resolution image "
                    "should be after the one of the overview of index {}".format(
                        len(overviews) - 1
                    )
                )

        for ix, dec in enumerate(overviews):
            with rasterio.open(src_path, OVERVIEW_LEVEL=ix) as ovr_dst:
                if ovr_dst.width >= 512 or ovr_dst.height >= 512:
                    if not ovr_dst.is_tiled:
                        errors.append("Overview of index {} is not tiled".format(ix))

    if warnings:
        click.secho("The following warnings were found:", fg="yellow", err=True)
        for w in warnings:
            click.echo("- " + w, err=True)
        click.echo(err=True)

    if errors:
        click.secho("The following errors were found:", fg="red", err=True)
        for e in errors:
            click.echo("- " + e, err=True)

        return False

    return True
