"""rio_cogeo.utils: Utility functions."""

import math

from rasterio.warp import calculate_default_transform
from rasterio.enums import MaskFlags, ColorInterp


def _meters_per_pixel(zoom, lat):
    """
    Return the pixel resolution for a given mercator tile zoom and lattitude.

    Parameters
    ----------
    zoom: int
        Mercator zoom level
    lat: float
        Latitude in decimal degree

    Returns
    -------
    Pixel resolution in meters

    """
    return (math.cos(lat * math.pi / 180.0) * 2 * math.pi * 6378137) / (256 * 2 ** zoom)


def get_max_zoom(src_dst, snap=0.5, max_z=23):
    """
    Calculate raster max zoom level.

    Parameters
    ----------
    src: rasterio.io.DatasetReader
        Rasterio io.DatasetReader object
    snap: float or None
        0   = snap to the next higher mercator zoom level resolution
        0.5 = snap to the closest mercator resolution
        1   = snap to next lower mercator zoom level resolution
    max_z: int, optional (default: 23)
        Max mercator zoom level allowed

    Returns
    -------
    Pixel resolution in meters

    """
    dst_affine, w, h = calculate_default_transform(
        src_dst.crs, "epsg:3857", src_dst.width, src_dst.height, *src_dst.bounds
    )

    res_max = max(abs(dst_affine[0]), abs(dst_affine[4]))

    tgt_z = max_z
    mpp = 0.0

    # loop through the pyramid to file the closest z level
    for z in range(1, max_z):
        mpp = _meters_per_pixel(z, 0)
        if (mpp - ((mpp / 2) * snap)) < res_max:
            tgt_z = z
            break

    return tgt_z


def get_maximum_overview_level(src_dst, minsize=512):
    """Calculate the maximum overview level."""
    nlevel = 0
    overview = 1

    while min(src_dst.width // overview, src_dst.height // overview) > minsize:
        overview *= 2
        nlevel += 1

    return nlevel


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
    if any([MaskFlags.per_dataset in flags for flags in src_dst.mask_flag_enums]):
        return True
    return False
