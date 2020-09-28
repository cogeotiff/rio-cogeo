"""rio_cogeo.utils: Utility functions."""

import math
from typing import Dict, Tuple

import mercantile
from rasterio.crs import CRS
from rasterio.enums import ColorInterp, MaskFlags
from rasterio.enums import Resampling as ResamplingEnums
from rasterio.rio.overview import get_maximum_overview_level
from rasterio.transform import Affine
from rasterio.warp import calculate_default_transform, transform_bounds
from supermercado.burntiles import tile_extrema


def _meters_per_pixel(zoom, lat=0.0, tilesize=256):
    """
    Return the pixel resolution for a given mercator tile zoom and lattitude.

    Parameters
    ----------
    zoom: int
        Mercator zoom level
    lat: float, optional
        Latitude in decimal degree (default: 0)
    tilesize: int, optional
        Mercator tile size (default: 256).

    Returns
    -------
    Pixel resolution in meters

    """
    return (math.cos(lat * math.pi / 180.0) * 2 * math.pi * 6378137) / (
        tilesize * 2 ** zoom
    )


def zoom_for_pixelsize(pixel_size, max_z=24, tilesize=256):
    """
    Get mercator zoom level corresponding to a pixel resolution.

    Freely adapted from
    https://github.com/OSGeo/gdal/blob/b0dfc591929ebdbccd8a0557510c5efdb893b852/gdal/swig/python/scripts/gdal2tiles.py#L294

    Parameters
    ----------
    pixel_size: float
        Pixel size
    max_z: int, optional (default: 24)
        Max mercator zoom level allowed
    tilesize: int, optional
        Mercator tile size (default: 256).

    Returns
    -------
    Mercator zoom level corresponding to the pixel resolution

    """
    for z in range(max_z):
        if pixel_size > _meters_per_pixel(z, 0, tilesize=tilesize):
            return max(0, z - 1)  # We don't want to scale up

    return max_z - 1


def get_zooms(src_dst, lat=0.0, tilesize=256) -> Tuple[int, int]:
    """
    Calculate raster max zoom level.

    Parameters
    ----------
    src: rasterio.io.DatasetReader
        Rasterio io.DatasetReader object
    lat: float, optional
        Center latitude of the dataset. This is only needed in case you want to
        apply latitude correction factor to ensure consitent maximum zoom level
        (default: 0.0).
    tilesize: int, optional
        Mercator tile size (default: 256).

    Returns
    -------
    max_zoom: int
        Max zoom level.

    """
    dst_affine, w, h = calculate_default_transform(
        src_dst.crs, "epsg:3857", src_dst.width, src_dst.height, *src_dst.bounds
    )

    native_resolution = max(abs(dst_affine[0]), abs(dst_affine[4]))

    # Correction factor for web-mercator projection latitude distortion
    latitude_correction_factor = math.cos(math.radians(lat))
    corrected_resolution = native_resolution * latitude_correction_factor

    max_zoom = zoom_for_pixelsize(corrected_resolution, tilesize=tilesize)
    overview_level = get_maximum_overview_level(w, h, minsize=tilesize)

    ovr_resolution = corrected_resolution * (2 ** overview_level)

    min_zoom = zoom_for_pixelsize(ovr_resolution, tilesize=tilesize)

    return (min_zoom, max_zoom)


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


def get_web_optimized_params(
    src_dst,
    tilesize=256,
    latitude_adjustment: bool = True,
    warp_resampling: str = "nearest",
    grid_crs=CRS.from_epsg(3857),
) -> Dict:
    """Return VRT parameters for a WebOptimized COG."""
    bounds = list(
        transform_bounds(
            src_dst.crs, CRS.from_epsg(4326), *src_dst.bounds, densify_pts=21
        )
    )
    center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2]

    lat = 0 if latitude_adjustment else center[1]
    _, max_zoom = get_zooms(src_dst, lat=lat, tilesize=tilesize)

    extrema = tile_extrema(bounds, max_zoom)

    left, _, _, top = mercantile.xy_bounds(
        extrema["x"]["min"], extrema["y"]["min"], max_zoom
    )
    vrt_res = _meters_per_pixel(max_zoom, 0, tilesize=tilesize)
    vrt_transform = Affine(vrt_res, 0, left, 0, -vrt_res, top)

    vrt_width = (extrema["x"]["max"] - extrema["x"]["min"]) * tilesize
    vrt_height = (extrema["y"]["max"] - extrema["y"]["min"]) * tilesize

    return dict(
        crs=grid_crs,
        transform=vrt_transform,
        width=vrt_width,
        height=vrt_height,
        resampling=ResamplingEnums[warp_resampling],
    )
