"""rio_cogeo: Cloud Optimized GeoTIFF creation and validation plugin for rasterio."""

from .cogeo import cog_info, cog_translate, cog_validate  # noqa
from .profiles import cog_profiles  # noqa

__version__ = "3.1.0"
