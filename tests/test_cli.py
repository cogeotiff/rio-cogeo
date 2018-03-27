"""tests rio_cogeo.cogeo."""

import os

# from mock import patch

from click.testing import CliRunner

import rasterio
from rio_cogeo.scripts.cli import cogeo

raster_path_rgb = os.path.join(os.path.dirname(__file__), 'fixtures', 'image_rgb.tif')
raster_path_rgba = os.path.join(os.path.dirname(__file__), 'fixtures', 'image_rgba.tif')


def test_cogeo_valid():
    """Should work as expected."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgb, 'output.tif'])
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open('output.tif') as src:
            assert src.height == 512
            assert src.width == 512
            assert src.meta['dtype'] == 'uint8'
            assert not src.is_tiled  # Because blocksize is 512 and the file is 512, the output is not tiled
            assert src.compression.name == 'jpeg'
            assert src.profile['blockxsize'] == '512'
            assert src.profile['blockysize'] == '512'
            assert src.profile['photometric'] == 'ycbcr'
            assert src.profile['interleave'] == 'pixel'
            assert src.overviews(1) == [2, 4, 8, 16, 32, 64]


def test_cogeo_validbidx():
    """Should work as expected."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgb, 'output.tif', '-b', '1', '-p', 'raw'])
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open('output.tif') as src:
            assert src.count == 1


def test_cogeo_validInvalidbidx():
    """Should exit with invalid band indexes."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgb, 'output.tif', '-b', '0'])
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_validInvalidbidxString():
    """Should exit with invalid band indexes."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgb, 'output.tif', '-b', 'a'])
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_validAlpha():
    """Should work as expected."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgba, 'output.tif', '-b', '1,2,3', '--alpha', 4])
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open('output.tif') as src:
            assert src.count == 3


def test_cogeo_validnodata():
    """Should work as expected."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgb, 'output.tif', '--nodata', 0])
        assert not result.exception
        assert result.exit_code == 0


def test_cogeo_validalpahnodata():
    """Should exit with incompatible option."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgba, 'output.tif', '--nodata', 0, '--alpha', 4])
        assert result.exception
        assert result.exit_code == 1


def test_cogeo_validGdalOptions():
    """Should work as expected."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cogeo, [raster_path_rgb, 'output.tif', '-p', 'raw', '--co', 'COMPRESS=DEFLATE'])
        assert not result.exception
        assert result.exit_code == 0
        with rasterio.open('output.tif') as src:
            assert src.compression.name == 'deflate'
            assert src.profile['blockxsize'] == '512'
            assert src.profile['blockysize'] == '512'
            assert src.profile['photometric'] == 'rgb'
