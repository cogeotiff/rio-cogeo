"""rio_cogeo.utils: Utility functions."""

from typing import Dict, Optional, Tuple, Union

import morecantile
from rasterio.crs import CRS
from rasterio.enums import ColorInterp, MaskFlags
from rasterio.io import DatasetReader, DatasetWriter
from rasterio.rio.overview import get_maximum_overview_level
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from rasterio.warp import calculate_default_transform, transform_bounds


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
    if src_dst.crs != tms.crs:
        aff, w, h = calculate_default_transform(
            src_dst.crs, tms.crs, src_dst.width, src_dst.height, *src_dst.bounds,
        )
    else:
        aff = list(src_dst.transform)
        w = src_dst.width
        h = src_dst.height

    resolution = max(abs(aff[0]), abs(aff[4]))

    max_zoom = tms.zoom_for_res(
        resolution, max_z=30, zoom_level_strategy=zoom_level_strategy,
    )

    overview_level = get_maximum_overview_level(w, h, minsize=tilesize)
    ovr_resolution = resolution * (2 ** overview_level)
    min_zoom = tms.zoom_for_res(ovr_resolution, max_z=30)

    return (min_zoom, max_zoom)


def get_web_optimized_params(
    src_dst,
    zoom_level_strategy: str = "auto",
    aligned_levels: Optional[int] = None,
    tms: morecantile.TileMatrixSet = morecantile.tms.get("WebMercatorQuad"),
) -> Dict:
    """Return VRT parameters for a WebOptimized COG."""
    bounds = list(
        transform_bounds(
            src_dst.crs, CRS.from_epsg(4326), *src_dst.bounds, densify_pts=21
        )
    )

    if src_dst.crs != tms.crs:
        aff, w, h = calculate_default_transform(
            src_dst.crs, tms.crs, src_dst.width, src_dst.height, *src_dst.bounds,
        )
    else:
        aff = list(src_dst.transform)

    resolution = max(abs(aff[0]), abs(aff[4]))

    max_zoom = tms.zoom_for_res(
        resolution, max_z=30, zoom_level_strategy=zoom_level_strategy,
    )

    aligned_levels = aligned_levels or 0
    base_zoom = max_zoom - aligned_levels

    ul_tile = tms.tile(bounds[0], bounds[3], base_zoom)
    w, _, _, n = tms.xy_bounds(ul_tile.x, ul_tile.y, ul_tile.z)

    vrt_res = tms._resolution(tms.matrix(max_zoom))
    vrt_transform = Affine(vrt_res, 0, w, 0, -vrt_res, n)

    lr_tile = tms.tile(bounds[2], bounds[1], base_zoom)
    e, _, _, s = tms.xy_bounds(lr_tile.x + 1, lr_tile.y + 1, lr_tile.z)

    vrt_width = max(1, round((e - w) / vrt_transform.a))
    vrt_height = max(1, round((s - n) / vrt_transform.e))

    return dict(
        crs=tms.crs, transform=vrt_transform, width=vrt_width, height=vrt_height,
    )
