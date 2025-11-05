"""``pytest`` configuration."""

import os

import pytest
import rasterio
from rasterio.env import GDALVersion

with rasterio.Env() as env:
    drivers = env.drivers()

# Define helpers to skip tests based on GDAL version
gdal_version = GDALVersion.runtime()

webp_tiff_path_rgb = os.path.join(
    os.path.dirname(__file__), "fixtures", "image_webp.tif"
)

has_webp = False
try:
    with rasterio.open(webp_tiff_path_rgb) as src:
        pass

    has_webp = True

except rasterio.RasterioIOError:
    has_webp = False


requires_webp = pytest.mark.skipif(
    has_webp is False, reason="Only relevant if WEBP drivers is supported"
)

requires_gdal31 = pytest.mark.skipif(
    not gdal_version.at_least("3.1"), reason="Requires GDAL 3.1.x"
)

requires_gdal35 = pytest.mark.skipif(
    not gdal_version.at_least("3.5"), reason="Requires GDAL 3.5.x"
)

requires_gdal311 = pytest.mark.skipif(
    not gdal_version.at_least("3.11"), reason="Requires GDAL 3.11.x"
)


@pytest.fixture
def runner():
    """CLI Runner fixture."""
    from click.testing import CliRunner

    return CliRunner()
