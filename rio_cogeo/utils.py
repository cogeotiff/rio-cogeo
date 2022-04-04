"""rio_cogeo.utils: Utility functions."""

from typing import Dict, Optional, Tuple, Union

import morecantile
from rasterio.enums import ColorInterp, MaskFlags
from rasterio.io import DatasetReader, DatasetWriter
from rasterio.rio.overview import get_maximum_overview_level
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from rasterio.warp import calculate_default_transform


def has_alpha_band(src_dst: Union[DatasetReader, DatasetWriter, WarpedVRT]):
    """Check for alpha band or mask in source."""
    if (
        any([MaskFlags.alpha in flags for flags in src_dst.mask_flag_enums])
        or ColorInterp.alpha in src_dst.colorinterp
    ):
        return True
    return False


def has_mask_band(src_dst):
    """Check for mask band in source."""
    if any(
        [
            (MaskFlags.per_dataset in flags and MaskFlags.alpha not in flags)
            for flags in src_dst.mask_flag_enums
        ]
    ):
        return True
    return False


def non_alpha_indexes(src_dst: Union[DatasetReader, DatasetWriter, WarpedVRT]) -> Tuple:
    """Return indexes of non-alpha bands."""
    return tuple(
        b
        for ix, b in enumerate(src_dst.indexes)
        if (
            src_dst.mask_flag_enums[ix] is not MaskFlags.alpha
            and src_dst.colorinterp[ix] is not ColorInterp.alpha
        )
    )


def get_zooms(
    src_dst: Union[DatasetReader, DatasetWriter, WarpedVRT],
    tilesize: int = 256,
    tms: morecantile.TileMatrixSet = morecantile.tms.get("WebMercatorQuad"),
    zoom_level_strategy: str = "auto",
) -> Tuple[int, int]:
    """Calculate raster min/max zoom level."""
    # If the raster is not in the TMS CRS we calculate its projected properties (height, width, resolution)
    if src_dst.crs != tms.rasterio_crs:
        aff, w, h = calculate_default_transform(
            src_dst.crs,
            tms.rasterio_crs,
            src_dst.width,
            src_dst.height,
            *src_dst.bounds,
        )
    else:
        aff = list(src_dst.transform)
        w = src_dst.width
        h = src_dst.height

    resolution = max(abs(aff[0]), abs(aff[4]))

    # The maxzoom is defined by finding the minimum difference between
    # the raster resolution and the zoom level resolution
    max_zoom = tms.zoom_for_res(
        resolution,
        max_z=30,
        zoom_level_strategy=zoom_level_strategy,
    )

    # The minzoom is defined by the resolution of the maximum theoretical overview level
    max_possible_overview_level = get_maximum_overview_level(w, h, minsize=tilesize)
    ovr_resolution = resolution * (2**max_possible_overview_level)
    min_zoom = tms.zoom_for_res(ovr_resolution, max_z=30)

    return (min_zoom, max_zoom)


def get_web_optimized_params(
    src_dst,
    zoom_level_strategy: str = "auto",
    zoom_level: Optional[int] = None,
    aligned_levels: Optional[int] = None,
    tms: morecantile.TileMatrixSet = morecantile.tms.get("WebMercatorQuad"),
) -> Dict:
    """Return VRT parameters for a WebOptimized COG."""
    if src_dst.crs != tms.rasterio_crs:
        with WarpedVRT(src_dst, crs=tms.rasterio_crs) as vrt:
            bounds = vrt.bounds
            aff = list(vrt.transform)
    else:
        bounds = src_dst.bounds
        aff = list(src_dst.transform)

    resolution = max(abs(aff[0]), abs(aff[4]))

    if zoom_level is None:
        # find max zoom (closest to the raster resolution)
        max_zoom = tms.zoom_for_res(
            resolution,
            max_z=30,
            zoom_level_strategy=zoom_level_strategy,
        )
    else:
        max_zoom = zoom_level

    # defined the zoom level we want to align the raster
    aligned_levels = aligned_levels or 0
    base_zoom = max_zoom - aligned_levels

    # find new raster bounds (bounds of UL tile / LR tile)
    ul_tile = tms._tile(bounds[0], bounds[3], base_zoom)
    w, _, _, n = tms.xy_bounds(ul_tile)

    # The output resolution should match the TMS resolution at MaxZoom
    vrt_res = tms._resolution(tms.matrix(max_zoom))

    # Output transform is built from the origin (UL tile) and output resolution
    vrt_transform = Affine(vrt_res, 0, w, 0, -vrt_res, n)

    lr_tile = tms._tile(bounds[2], bounds[1], base_zoom)
    e, _, _, s = tms.xy_bounds(
        morecantile.Tile(lr_tile.x + 1, lr_tile.y + 1, lr_tile.z)
    )

    vrt_width = max(1, round((e - w) / vrt_transform.a))
    vrt_height = max(1, round((s - n) / vrt_transform.e))

    return dict(
        crs=tms.rasterio_crs,
        transform=vrt_transform,
        width=vrt_width,
        height=vrt_height,
    )
