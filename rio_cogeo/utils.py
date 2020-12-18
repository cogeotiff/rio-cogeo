"""rio_cogeo.utils: Utility functions."""

from typing import Dict, Optional, Tuple

import morecantile
from rasterio.crs import CRS
from rasterio.enums import ColorInterp, MaskFlags
from rasterio.enums import Resampling as ResamplingEnums
from rasterio.rio.overview import get_maximum_overview_level
from rasterio.transform import Affine
from rasterio.warp import calculate_default_transform, transform_bounds


def has_alpha_band(src_dst):
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


def get_zooms(
    src_dst,
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
    tilesize=256,
    warp_resampling: str = "nearest",
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
    min_zoom, max_zoom = get_zooms(
        src_dst, tilesize=tilesize, tms=tms, zoom_level_strategy=zoom_level_strategy,
    )

    if aligned_levels is not None:
        min_zoom = max_zoom - aligned_levels

    ul_tile = tms.tile(bounds[0], bounds[3], min_zoom)
    left, _, _, top = tms.xy_bounds(ul_tile.x, ul_tile.y, ul_tile.z)

    vrt_res = tms._resolution(tms.matrix(max_zoom))
    vrt_transform = Affine(vrt_res, 0, left, 0, -vrt_res, top)

    lr_tile = tms.tile(bounds[2], bounds[1], min_zoom)
    extrema = {
        "x": {"min": ul_tile.x, "max": lr_tile.x + 1},
        "y": {"min": ul_tile.y, "max": lr_tile.y + 1},
    }
    vrt_width = (
        (extrema["x"]["max"] - extrema["x"]["min"])
        * tilesize
        * 2 ** (max_zoom - min_zoom)
    )
    vrt_height = (
        (extrema["y"]["max"] - extrema["y"]["min"])
        * tilesize
        * 2 ** (max_zoom - min_zoom)
    )

    return dict(
        crs=tms.crs,
        transform=vrt_transform,
        width=vrt_width,
        height=vrt_height,
        resampling=ResamplingEnums[warp_resampling],
    )
