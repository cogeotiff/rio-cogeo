"""Rio_cogeo.scripts.cli."""

import os
import click

from rasterio.rio import options
from rasterio.enums import Resampling

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles


class CustomType:
    """Click CustomType."""

    class BdxParamType(click.ParamType):
        """Band inddex type."""

        name = "bidx"

        def convert(self, value, param, ctx):
            """Validate and parse band index."""
            try:
                bands = [int(x) for x in value.split(",")]
                assert all(b > 0 for b in bands)
                return bands

            except (ValueError, AttributeError, AssertionError):
                raise click.ClickException(
                    "bidx must be a string of comma-separated integers (> 0), "
                    "representing the band indexes."
                )

    bidx = BdxParamType()


@click.command()
@options.file_in_arg
@options.file_out_arg
@click.option("--bidx", "-b", type=CustomType.bidx, help="Band index to copy")
@click.option(
    "--cog-profile",
    "-p",
    "cogeo_profile",
    type=click.Choice(cog_profiles.keys()),
    default="ycbcr",
    help="CloudOptimized GeoTIFF profile (default: ycbcr)",
)
@click.option(
    "--nodata", type=int, help="Force mask creation from a given nodata value"
)
@click.option(
    "--alpha", type=int, help="Force mask creation from a given alpha band number"
)
@click.option(
    "--overview-level", type=int, default=6, help="Overview level (default: 6)"
)
@click.option(
    "--overview-resampling",
    help="Resampling algorithm.",
    type=click.Choice(
        [it.name for it in Resampling if it.value in [0, 1, 2, 3, 4, 5, 6, 7]]
    ),
    default="nearest",
)
@click.option("--threads", type=int, default=8)
@options.creation_options
def cogeo(
    input,
    output,
    bidx,
    cogeo_profile,
    nodata,
    alpha,
    overview_level,
    overview_resampling,
    threads,
    creation_options,
):
    """Create Cloud Optimized Geotiff."""
    if nodata is not None and alpha is not None:
        raise click.ClickException('Incompatible options "alpha" and "nodata"')

    output_profile = cog_profiles.get(cogeo_profile)
    output_profile.update(dict(BIGTIFF=os.environ.get("BIGTIFF", "IF_SAFER")))
    if creation_options:
        output_profile.update(creation_options)

    block_size = min(output_profile["blockxsize"], output_profile["blockysize"])

    config = dict(
        NUM_THREADS=threads,
        GDAL_TIFF_INTERNAL_MASK=os.environ.get("GDAL_TIFF_INTERNAL_MASK", True),
        GDAL_TIFF_OVR_BLOCKSIZE=os.environ.get("GDAL_TIFF_OVR_BLOCKSIZE", block_size),
    )

    cog_translate(
        input,
        output,
        output_profile,
        bidx,
        nodata,
        alpha,
        overview_level,
        overview_resampling,
        config,
    )
