"""rio_cogeo.utils: Utility functions."""

import math

from rasterio.warp import calculate_default_transform
from rasterio.enums import MaskFlags, ColorInterp


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


def get_max_zoom(src_dst, lat=0.0, tilesize=256):
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
    return max_zoom


def get_maximum_overview_level(src_dst, minsize=512):
    """
    Calculate the maximum overview level.

    Attributes
    ----------
    src_dst : rasterio.io.DatasetReader
        Rasterio io.DatasetReader object.
    minsize : int (default: 512)
        Minimum overview size.

    Returns
    -------
    nlevel: int
        overview level.

    """
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
