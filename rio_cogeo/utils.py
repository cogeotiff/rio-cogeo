"""rio_cogeo.utils: Utility functions."""

import math

import rasterio
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
    pixel resolution in meters

    """
    return (math.cos(lat * math.pi / 180.0) * 2 * math.pi * 6378137) / (256 * 2 ** zoom)


def get_max_zoom(src, snap=0.5, max_z=23):
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
    max_z: int
        max mercator zoom level allowed
        [DEFAULT = 23]

    Returns
    -------
    pixel resolution in meters

    """
    dst_affine, w, h = calculate_default_transform(
        src.crs, "epsg:3857", src.width, src.height, *src.bounds
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


def has_alpha_band(src):
    """
    Check for alpha band or mask in a dataset.

    Parameters
    ----------
    src: rasterio.io.DatasetReader
        Rasterio io.DatasetReader object

    Returns
    -------
    bool

    """
    if (
        any([MaskFlags.alpha in flags for flags in src.mask_flag_enums])
        or ColorInterp.alpha in src.colorinterp
    ):
        return True
    return False


def get_maximum_overview_level(src_path, minsize=512):
    """
    Calculate the maximum overview level.

    Parameters
    ----------
    src_path: str
        Input dataset path
    minsize: int
        Minimum overview size
        [DEFAULT = 512]

    Returns
    -------
    nlevel: int
        maximum overview level

    """
    with rasterio.open(src_path) as src:
        width = src.width
        height = src.height

    nlevel = 0
    overview = 1

    while min(width // overview, height // overview) > minsize:
        overview *= 2
        nlevel += 1

    return nlevel
