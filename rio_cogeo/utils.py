"""rio_cogeo.utils: Utility functions."""

import rasterio


def get_maximum_overview_level(src_path, minsize=512):
    """Calculate the maximum overview level."""
    with rasterio.open(src_path) as src:
        width = src.width
        height = src.height

    nlevel = 0
    overview = 1

    while min(width // overview, height // overview) > minsize:
        overview *= 2
        nlevel += 1

    return nlevel
