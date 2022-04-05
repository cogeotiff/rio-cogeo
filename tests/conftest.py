"""``pytest`` configuration."""


import pytest
import rasterio
from rasterio.env import GDALVersion

with rasterio.Env() as env:
    drivers = env.drivers()

# Define helpers to skip tests based on GDAL version
gdal_version = GDALVersion.runtime()

requires_webp = pytest.mark.skipif(
    "WEBP" not in drivers.keys(), reason="Only relevant if WEBP drivers is supported"
)

requires_gdal31 = pytest.mark.skipif(
    not gdal_version.at_least("3.1"), reason="Requires GDAL 3.1.x"
)

requires_gdal35 = pytest.mark.skipif(
    not gdal_version.at_least("3.5"), reason="Requires GDAL 3.5.x"
)


@pytest.fixture
def runner():
    """CLI Runner fixture."""
    from click.testing import CliRunner

    return CliRunner()
