"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import os
import sys

import click

import numpy

import rasterio
from rasterio.io import MemoryFile
from rasterio.env import GDALVersion
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
    overview_resampling="nearest",
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
                            mem.write_mask(mask_value, window=w)

                    overviews = [2 ** j for j in range(1, overview_level + 1)]

                    mem.build_overviews(overviews, Resampling[overview_resampling])
                    mem.update_tags(
                        OVR_RESAMPLING_ALG=Resampling[overview_resampling].name.upper()
                    )

                    copy(mem, dst_path, copy_src_overviews=True, **dst_kwargs)


def cog_validate(src_path):
    """
    Create Cloud Optimized Geotiff.

    Parameters
    ----------
    src_path : str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.

    This script is the rasterio equivalent of
    https://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/validate_cloud_optimized_geotiff.py

    """
    errors = []
    details = {}

    if not GDALVersion.runtime().at_least("2.2"):
        raise Exception("GDAL 2.2 or above required")

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
                errors.append(
                    "The file is greater than 512xH or 512xW, but has no overviews"
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

            # TODO: Check if the overviews are tiled
            # NOTE: There is currently no way to do that with rasterio
            # if check_tiled:
            #     block_size = ovr_band.GetBlockSize()
            #     if block_size[0] == ovr_band.XSize and block_size[0] > 1024:
            #         errors += [
            #             'Overview of index %d is not tiled' % i]

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
                "The offset of the first block of the main resolution image"
                "should be after the one of the overview of index {}".format(
                    len(overviews) - 1
                )
            )

    if errors:
        for e in errors:
            click.echo(e, err=True)

        return False

    return True
