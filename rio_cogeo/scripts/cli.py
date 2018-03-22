"""rio_cogeo.scripts.cli"""

import click

import rasterio

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles


class CustomType():

    class BdxParamType(click.ParamType):
        """Band Index Type
        """
        name = 'str'

        def convert(self, value, param, ctx):
            try:
                bands = [int(x) for x in value.split(',')]
                assert len(bands) in [1, 3]
                assert all(b > 0 for b in bands)
                return bands
            except (AttributeError, AssertionError):
                raise click.ClickException('bidx must be a string with 1 or 3 ints (> 0) comma-separated, '
                                           'representing the band indexes for R,G,B')

    bidx = BdxParamType()


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', required=True, type=click.Path())
@click.option('--bidx', '-b', type=CustomType.bidx, default='1,2,3', help='Band index to copy')
@click.option('--profile', '-p', type=str, default='ycbcr', help='COGEO profile (default: ycbcr)')
@click.option('--nodata', type=int, help='Force mask creation from a given nodata value')
@click.option('--alpha', type=int, help='Force mask creation from a given alpha band number')
@click.option('--overview-level', type=int, default=6, help='Overview level (default: 6)')
@click.option('--threads', type=int, default=8)
def cogeo(path, output, bidx, profile, nodata, alpha, overview_level, threads):
    """Create Cloud Optimized Geotiff
    """

    if nodata is not None and alpha:
        raise click.ClickException('Incompatible  option "alpha" and "nodata"')

    output_profile = cog_profiles.get(profile)

    gda_env = dict(
        GDAL_TIFF_INTERNAL_MASK=True,
        GDAL_TIFF_OVR_BLOCKSIZE=512,
        NUM_THREADS=threads)

    with rasterio.Env(**gda_env):
        cog_translate(path, output, output_profile, bidx, nodata, alpha, overview_level)
