"""rio_cogeo.cogeo: translate a file to a cloud optimized geotiff."""

import math
import os
import pathlib
import sys
import tempfile
import warnings
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import click
import morecantile
import rasterio
from rasterio.enums import ColorInterp
from rasterio.enums import Resampling as ResamplingEnums
from rasterio.env import GDALVersion
from rasterio.io import DatasetReader, DatasetWriter, MemoryFile
from rasterio.rio.overview import get_maximum_overview_level
from rasterio.shutil import copy
from rasterio.vrt import WarpedVRT

from rio_cogeo import models, utils
from rio_cogeo.errors import IncompatibleBlockRasterSize, IncompatibleOptions

IN_MEMORY_THRESHOLD = int(os.environ.get("IN_MEMORY_THRESHOLD", 10980 * 10980))


@contextmanager
def TemporaryRasterFile(dst_path: Union[str, pathlib.PurePath], suffix: str = ".tif"):
    """Create temporary file."""
    # For local file we should create temporary file in the same directory
    tmpdir = (
        None if not pathlib.Path(dst_path).is_file() else pathlib.Path(dst_path).parent
    )
    fileobj = tempfile.NamedTemporaryFile(dir=tmpdir, suffix=suffix, delete=False)
    fileobj.close()
    try:
        yield fileobj
    finally:
        os.remove(fileobj.name)


def cog_translate(  # noqa: C901
    source: Union[str, pathlib.PurePath, DatasetReader, DatasetWriter, WarpedVRT],
    dst_path: Union[str, pathlib.PurePath],
    dst_kwargs: Dict,
    indexes: Optional[Sequence[int]] = None,
    nodata: Optional[Union[str, int, float]] = None,
    dtype: Optional[str] = None,
    add_mask: bool = False,
    overview_level: Optional[int] = None,
    overview_resampling: str = "nearest",
    web_optimized: bool = False,
    tms: Optional[morecantile.TileMatrixSet] = None,
    zoom_level_strategy: str = "auto",
    zoom_level: Optional[int] = None,
    aligned_levels: Optional[int] = None,
    resampling: str = "nearest",
    in_memory: Optional[bool] = None,
    config: Optional[Dict] = None,
    allow_intermediate_compression: bool = False,
    forward_band_tags: bool = False,
    forward_ns_tags: bool = False,
    quiet: bool = False,
    temporary_compression: str = "DEFLATE",
    colormap: Optional[Dict] = None,
    additional_cog_metadata: Optional[Dict] = None,
    use_cog_driver: bool = False,
):
    """
    Create Cloud Optimized Geotiff.

    Parameters
    ----------
    source : str, PathLike object or rasterio.io.DatasetReader
        A dataset path, URL or rasterio.io.DatasetReader object.
        Will be opened in "r" mode.
    dst_path : str or PathLike object
        An output dataset path or or PathLike object.
        Will be opened in "w" mode.
    dst_kwargs: dict
        Output dataset creation options.
    indexes : tuple or int, optional
        Raster band indexes to copy.
    nodata, int, optional
        Overwrite nodata masking values for input dataset.
    dtype: str, optional
        Overwrite output data type. Default will be the input data type.
    add_mask, bool, optional
        Force output dataset creation with a mask.
    overview_level : int, optional (default: None)
        COGEO overview (decimation) level. By default, inferred from data size.
    overview_resampling : str, optional (default: "nearest")
        Resampling algorithm for overviews
    web_optimized: bool, optional (default: False)
        Create web-optimized cogeo.
    tms: morecantile.TileMatrixSet, optional (default: "WebMercatorQuad")
        TileMatrixSet to use for reprojection, resolution and alignment.
    zoom_level_strategy: str, optional (default: auto)
        Strategy to determine zoom level (same as in GDAL 3.2).
        LOWER will select the zoom level immediately below the theoretical computed non-integral zoom level, leading to subsampling.
        On the contrary, UPPER will select the immediately above zoom level, leading to oversampling.
        Defaults to AUTO which selects the closest zoom level.
        ref: https://gdal.org/drivers/raster/cog.html#raster-cog
    zoom_level: int, optional.
        Zoom level number (starting at 0 for coarsest zoom level). If this option is specified, `--zoom-level-strategy` is ignored.
    aligned_levels: int, optional.
        Number of overview levels for which GeoTIFF tile and tiles defined in the tiling scheme match.
        Default is to use the maximum overview levels. Note: GDAL use number of resolution levels instead of overview levels.
    resampling : str, optional (default: "nearest")
        Resampling algorithm.
    in_memory: bool, optional
        Force processing raster in memory (default: process in memory if small)
    config : dict
        Rasterio Env options.
    allow_intermediate_compression: bool, optional (default: False)
        Allow intermediate file compression to reduce memory/disk footprint.
        Note: This could reduce the speed of the process.
        Ref: https://github.com/cogeotiff/rio-cogeo/issues/103
    forward_band_tags:  bool, optional
        Forward band tags to output bands.
        Ref: https://github.com/cogeotiff/rio-cogeo/issues/19
    forward_ns_tags:  bool, optional
        Forward namespaces tags to output dataset.
    quiet: bool, optional (default: False)
        Mask processing steps.
    temporary_compression: str, optional
        Compression used for the intermediate file, default is deflate.
    colormap: dict, optional
        Overwrite or add a colormap to the output COG.
    additional_cog_metadata: dict, optional
        Additional dataset metadata to add to the COG.
    use_cog_driver: bool, optional (default: False)
        Use GDAL COG driver if set to True. COG driver is available starting with GDAL 3.1.

    """
    tms = tms or morecantile.tms.get("WebMercatorQuad")

    dst_kwargs = dst_kwargs.copy()

    if isinstance(indexes, int):
        indexes = (indexes,)

    config = config or {}
    with rasterio.Env(**config):
        with ExitStack() as ctx:
            if isinstance(source, (DatasetReader, DatasetWriter, WarpedVRT)):
                src_dst = source
            else:
                src_dst = ctx.enter_context(rasterio.open(source))

            meta = src_dst.meta
            indexes = indexes if indexes else src_dst.indexes
            nodata = nodata if nodata is not None else src_dst.nodata
            dtype = dtype if dtype else src_dst.dtypes[0]
            alpha = utils.has_alpha_band(src_dst)
            mask = utils.has_mask_band(src_dst)

            if colormap and len(indexes) > 1:
                raise IncompatibleOptions(
                    "Cannot add a colormap for multiple bands data."
                )

            if not add_mask and (
                (nodata is not None or alpha)
                and dst_kwargs.get("compress", "").lower() == "jpeg"
            ):
                warnings.warn(
                    "Nodata/Alpha band will be translated to an internal mask band.",
                )
                add_mask = True
                indexes = (
                    utils.non_alpha_indexes(src_dst)
                    if len(indexes) not in [1, 3]
                    else indexes
                )

            tilesize = min(int(dst_kwargs["blockxsize"]), int(dst_kwargs["blockysize"]))

            if src_dst.width < tilesize or src_dst.height < tilesize:
                tilesize = 2 ** int(math.log(min(src_dst.width, src_dst.height), 2))
                if tilesize < 64:
                    warnings.warn(
                        "Raster has dimension < 64px. Output COG cannot be tiled"
                        " and overviews cannot be added.",
                        IncompatibleBlockRasterSize,
                    )
                    dst_kwargs.pop("blockxsize", None)
                    dst_kwargs.pop("blockysize", None)
                    dst_kwargs.pop("tiled")
                    overview_level = 0

                else:
                    warnings.warn(
                        "Block Size are bigger than raster sizes. "
                        "Setting blocksize to {}".format(tilesize),
                        IncompatibleBlockRasterSize,
                    )
                    dst_kwargs["blockxsize"] = tilesize
                    dst_kwargs["blockysize"] = tilesize

            vrt_params = {
                "add_alpha": True,
                "dtype": dtype,
                "width": src_dst.width,
                "height": src_dst.height,
                "resampling": ResamplingEnums[resampling],
            }

            if nodata is not None:
                vrt_params.update(
                    dict(nodata=nodata, add_alpha=False, src_nodata=nodata)
                )

            if alpha:
                vrt_params.update(dict(add_alpha=False))

            if web_optimized and not use_cog_driver:
                params = utils.get_web_optimized_params(
                    src_dst,
                    zoom_level_strategy=zoom_level_strategy,
                    zoom_level=zoom_level,
                    aligned_levels=aligned_levels,
                    tms=tms,
                )
                vrt_params.update(**params)

            with WarpedVRT(src_dst, **vrt_params) as vrt_dst:
                meta = vrt_dst.meta
                meta["count"] = len(indexes)

                if add_mask:
                    meta.pop("nodata", None)
                    meta.pop("alpha", None)

                if (
                    dst_kwargs.get("photometric", "").upper() == "YCBCR"
                    and meta["count"] == 1
                ):
                    warnings.warn(
                        "PHOTOMETRIC=YCBCR not supported on a 1-band raster"
                        " and has been set to 'MINISBLACK'"
                    )
                    dst_kwargs["photometric"] = "MINISBLACK"

                meta.update(**dst_kwargs)
                meta.pop("compress", None)
                meta.pop("photometric", None)

                if allow_intermediate_compression:
                    meta["compress"] = temporary_compression

                if in_memory is None:
                    in_memory = vrt_dst.width * vrt_dst.height < IN_MEMORY_THRESHOLD

                if in_memory:
                    tmpfile = ctx.enter_context(MemoryFile())
                    tmp_dst = ctx.enter_context(tmpfile.open(**meta))
                else:
                    tmpfile = ctx.enter_context(TemporaryRasterFile(dst_path))
                    tmp_dst = ctx.enter_context(
                        rasterio.open(tmpfile.name, "w", **meta)
                    )

                # Transfer color interpolation
                if len(indexes) == 1 and (
                    vrt_dst.colorinterp[indexes[0] - 1] is not ColorInterp.palette
                ):
                    tmp_dst.colorinterp = [ColorInterp.gray]
                else:
                    tmp_dst.colorinterp = [vrt_dst.colorinterp[b - 1] for b in indexes]

                if colormap:
                    if tmp_dst.colorinterp[0] is not ColorInterp.palette:
                        tmp_dst.colorinterp = [ColorInterp.palette]
                        warnings.warn(
                            "Dataset color interpretation was set to `Palette`"
                        )
                    tmp_dst.write_colormap(1, colormap)

                elif tmp_dst.colorinterp[0] is ColorInterp.palette:
                    try:
                        tmp_dst.write_colormap(1, vrt_dst.colormap(1))
                    except ValueError:
                        warnings.warn(
                            "Dataset has `Palette` color interpretation"
                            " but is missing colormap information"
                        )

                wind = list(tmp_dst.block_windows(1))

                if not quiet:
                    click.echo("Reading input: {}".format(source), err=True)

                fout = ctx.enter_context(open(os.devnull, "w")) if quiet else sys.stderr
                with click.progressbar(wind, file=fout, show_percent=True) as windows:  # type: ignore
                    for _, w in windows:
                        matrix = vrt_dst.read(window=w, indexes=indexes)
                        tmp_dst.write(matrix, window=w)

                        if add_mask or mask:
                            # Cast mask to uint8 to fix rasterio 1.1.2 error (ref #115)
                            mask_value = vrt_dst.dataset_mask(window=w).astype("uint8")
                            tmp_dst.write_mask(mask_value, window=w)

                if overview_level is None:
                    overview_level = get_maximum_overview_level(
                        vrt_dst.width, vrt_dst.height, minsize=tilesize
                    )

                if not quiet and overview_level:
                    click.echo("Adding overviews...", err=True)

                overviews = [2**j for j in range(1, overview_level + 1)]
                tmp_dst.build_overviews(overviews, ResamplingEnums[overview_resampling])

                if not quiet:
                    click.echo("Updating dataset tags...", err=True)

                for i, b in enumerate(indexes):
                    tmp_dst.set_band_description(i + 1, src_dst.descriptions[b - 1])
                    if forward_band_tags:
                        tmp_dst.update_tags(bidx=i + 1, **src_dst.tags(b))

                tags = src_dst.tags()
                tags.update(
                    dict(
                        OVR_RESAMPLING_ALG=ResamplingEnums[
                            overview_resampling
                        ].name.upper()
                    )
                )
                if additional_cog_metadata:
                    tags.update(**additional_cog_metadata)

                if forward_ns_tags:
                    namespaces = src_dst.tag_namespaces()
                    for ns in namespaces:
                        if ns in ["DERIVED_SUBDATASETS", "IMAGE_STRUCTURE"]:
                            continue
                        tmp_dst.update_tags(ns=ns, **src_dst.tags(ns=ns))

                if web_optimized and not use_cog_driver:
                    default_zoom = tms.zoom_for_res(
                        max(tmp_dst.res),
                        max_z=30,
                        zoom_level_strategy=zoom_level_strategy,
                    )
                    dst_kwargs.update(
                        {
                            "@TILING_SCHEME_NAME": tms.identifier,
                            "@TILING_SCHEME_ZOOM_LEVEL": zoom_level
                            if zoom_level is not None
                            else default_zoom,
                        }
                    )

                    if aligned_levels:
                        dst_kwargs.update(
                            {"@TILING_SCHEME_ALIGNED_LEVELS": aligned_levels}
                        )

                tmp_dst.update_tags(**tags)
                tmp_dst._set_all_scales([vrt_dst.scales[b - 1] for b in indexes])
                tmp_dst._set_all_offsets([vrt_dst.offsets[b - 1] for b in indexes])

                if not quiet:
                    click.echo("Writing output to: {}".format(dst_path), err=True)

                if use_cog_driver:
                    if not GDALVersion.runtime().at_least("3.1"):
                        raise Exception(
                            "GDAL 3.1 or above required to use the COG driver."
                        )

                    dst_kwargs["driver"] = "COG"
                    if web_optimized:
                        dst_kwargs["TILING_SCHEME"] = (
                            "GoogleMapsCompatible"
                            if tms.identifier == "WebMercatorQuad"
                            else tms.identifier
                        )

                        if zoom_level is not None:
                            if not GDALVersion.runtime().at_least("3.5"):
                                warnings.warn(
                                    "ZOOM_LEVEL option is only available with GDAL >3.5."
                                )

                            dst_kwargs["ZOOM_LEVEL"] = zoom_level

                        dst_kwargs["ZOOM_LEVEL_STRATEGY"] = zoom_level_strategy

                        if aligned_levels is not None:
                            # GDAL uses Number of resolution (not overviews)
                            # See https://github.com/OSGeo/gdal/issues/5336#issuecomment-1042946603
                            dst_kwargs["aligned_levels"] = aligned_levels + 1

                    if add_mask and dst_kwargs.get("compress", "") != "JPEG":
                        warnings.warn(
                            "With GDAL COG driver, mask band will be translated to an alpha band."
                        )

                    dst_kwargs["overview_resampling"] = overview_resampling
                    dst_kwargs["warp_resampling"] = resampling
                    dst_kwargs["blocksize"] = tilesize
                    dst_kwargs.pop("blockxsize", None)
                    dst_kwargs.pop("blockysize", None)
                    dst_kwargs.pop("tiled", None)
                    dst_kwargs.pop("interleave", None)
                    dst_kwargs.pop("photometric", None)

                    copy(tmp_dst, dst_path, **dst_kwargs)

                else:
                    copy(tmp_dst, dst_path, copy_src_overviews=True, **dst_kwargs)


def cog_validate(  # noqa: C901
    src_path: Union[str, pathlib.PurePath],
    strict: bool = False,
    config: Optional[Dict] = None,
    quiet: bool = False,
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Cloud Optimized Geotiff.

    This script is the rasterio equivalent of
    https://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/validate_cloud_optimized_geotiff.py

    Parameters
    ----------
    src_path: str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.
    strict: bool
        Treat warnings as errors
    quiet: bool
        Remove standard outputs

    Returns
    -------
    is_valid: bool
        True is src_path is a valid COG.
    errors: list
        List of validation errors.
    warnings: list
        List of validation warnings.

    """
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}

    config = config or {}

    if not GDALVersion.runtime().at_least("2.2"):
        raise Exception("GDAL 2.2 or above required")

    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:
            if not src.driver == "GTiff":
                errors.append("The file is not a GeoTIFF")
                if not quiet:
                    click.secho("The following errors were found:", fg="red", err=True)
                    for e in errors:
                        click.echo("- " + e, err=True)

                return False, errors, warnings

            if any(pathlib.Path(x).suffix == ".ovr" for x in src.files):
                errors.append(
                    "Overviews found in external .ovr file. They should be internal"
                )

            overviews = src.overviews(1)
            if src.width > 512 and src.height > 512:
                if not src.is_tiled:
                    errors.append(
                        "The file is greater than 512xH or 512xW, but is not tiled"
                    )

                if not overviews:
                    warnings.append(
                        "The file is greater than 512xH or 512xW, it is recommended "
                        "to include internal overviews"
                    )

            ifd_offset = int(src.get_tag_item("IFD_OFFSET", "TIFF", bidx=1))
            # Starting from GDAL 3.1, GeoTIFF and COG have ghost headers
            # e.g:
            # """
            # GDAL_STRUCTURAL_METADATA_SIZE=000140 bytes
            # LAYOUT=IFDS_BEFORE_DATA
            # BLOCK_ORDER=ROW_MAJOR
            # BLOCK_LEADER=SIZE_AS_UINT4
            # BLOCK_TRAILER=LAST_4_BYTES_REPEATED
            # KNOWN_INCOMPATIBLE_EDITION=NO
            # """
            #
            # This header should be < 200bytes
            if ifd_offset > 300:
                errors.append(
                    f"The offset of the main IFD should be < 300. It is {ifd_offset} instead"
                )

            ifd_offsets = [ifd_offset]
            details["ifd_offsets"] = {}
            details["ifd_offsets"]["main"] = ifd_offset

            if overviews and overviews != sorted(overviews):
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

            block_offset = src.get_tag_item("BLOCK_OFFSET_0_0", "TIFF", bidx=1)

            data_offset = int(block_offset) if block_offset else 0
            data_offsets = [data_offset]
            details["data_offsets"] = {}
            details["data_offsets"]["main"] = data_offset

            for ix, dec in enumerate(overviews):
                block_offset = src.get_tag_item(
                    "BLOCK_OFFSET_0_0", "TIFF", bidx=1, ovr=ix
                )
                data_offset = int(block_offset) if block_offset else 0
                data_offsets.append(data_offset)
                details["data_offsets"]["overview_{}".format(ix)] = data_offset

            if data_offsets[-1] != 0 and data_offsets[-1] < ifd_offsets[-1]:
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
                if ovr_dst.width > 512 and ovr_dst.height > 512:
                    if not ovr_dst.is_tiled:
                        errors.append("Overview of index {} is not tiled".format(ix))

    if warnings and not quiet:
        click.secho("The following warnings were found:", fg="yellow", err=True)
        for w in warnings:
            click.echo("- " + w, err=True)
        click.echo(err=True)

    if errors and not quiet:
        click.secho("The following errors were found:", fg="red", err=True)
        for e in errors:
            click.echo("- " + e, err=True)

    is_valid = False if errors or (warnings and strict) else True

    return is_valid, errors, warnings


def cog_info(
    src_path: Union[str, pathlib.PurePath],
    strict: bool = False,
    config: Optional[Dict] = None,
    quiet: bool = True,
) -> models.Info:
    """Get general info and validate Cloud Optimized Geotiff."""
    config = config or {}

    is_valid, validation_errors, validation_warnings = cog_validate(
        src_path, strict=strict, config=config, quiet=quiet
    )

    with rasterio.Env(**config):
        with rasterio.open(src_path) as src_dst:
            driver = src_dst.driver
            compression = src_dst.compression.value if src_dst.compression else None
            colorspace = src_dst.photometric.value if src_dst.photometric else None
            overviews = src_dst.overviews(1)

            tags = {"Image Metadata": src_dst.tags()}
            namespaces = src_dst.tag_namespaces()
            for ns in namespaces:
                if ns in ["DERIVED_SUBDATASETS"]:
                    continue
                tags.update({str.title(ns).replace("_", " "): src_dst.tags(ns=ns)})

            band_metadata = {
                f"Band {ix}": models.BandMetadata(
                    **{
                        "Description": src_dst.descriptions[ix - 1],
                        "ColorInterp": src_dst.colorinterp[ix - 1].name,
                        "Offset": src_dst.offsets[ix - 1],
                        "Scale": src_dst.scales[ix - 1],
                        "Metadata": src_dst.tags(ix),
                    }
                )
                for ix in src_dst.indexes
            }

            try:
                colormap = src_dst.colormap(1)
            except ValueError:
                colormap = None

            profile = models.Profile(
                Bands=src_dst.count,
                Width=src_dst.width,
                Height=src_dst.height,
                Tiled=src_dst.is_tiled,
                Dtype=src_dst.dtypes[0],
                Interleave=src_dst.interleaving.value
                if src_dst.interleaving
                else "UNKNOWN",
                AlphaBand=utils.has_alpha_band(src_dst),
                InternalMask=utils.has_mask_band(src_dst),
                Nodata=src_dst.nodata,
                ColorInterp=tuple([color.name for color in src_dst.colorinterp]),
                ColorMap=colormap is not None,
                Scales=src_dst.scales,
                Offsets=src_dst.offsets,
            )

            try:
                crs = (
                    f"EPSG:{src_dst.crs.to_epsg()}"
                    if src_dst.crs.to_epsg()
                    else src_dst.crs.to_wkt()
                )
            except AttributeError:
                crs = None

            minzoom: Optional[int] = None
            maxzoom: Optional[int] = None
            try:
                minzoom, maxzoom = utils.get_zooms(src_dst)
            except Exception:
                pass

            geo = models.Geo(
                CRS=crs,
                BoundingBox=tuple(src_dst.bounds),
                Origin=(src_dst.transform.c, src_dst.transform.f),
                Resolution=(src_dst.transform.a, src_dst.transform.e),
                MinZoom=minzoom,
                MaxZoom=maxzoom,
            )

            ifds = [
                models.IFD(
                    Level=0,
                    Width=src_dst.width,
                    Height=src_dst.height,
                    Blocksize=src_dst.block_shapes[0],
                    Decimation=0,
                )
            ]

        for ix, decim in enumerate(overviews):
            with rasterio.open(src_path, OVERVIEW_LEVEL=ix) as ovr_dst:
                ifds.append(
                    models.IFD(
                        Level=ix + 1,
                        Width=ovr_dst.width,
                        Height=ovr_dst.height,
                        Blocksize=ovr_dst.block_shapes[0],
                        Decimation=decim,
                    )
                )

    return models.Info(
        Path=str(src_path),
        Driver=driver,
        COG=is_valid,
        Compression=compression,
        ColorSpace=colorspace,
        COG_errors=validation_errors or None,
        COG_warnings=validation_warnings or None,
        Profile=profile,
        GEO=geo,
        Tags=tags,
        Band_Metadata=band_metadata,
        IFD=ifds,
    )
