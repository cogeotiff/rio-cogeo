"""Rio_cogeo.scripts.cli."""

import os
import warnings

import click
import numpy

from rasterio.rio import options
from rasterio.enums import Resampling as ResamplingEnums

from rio_cogeo import version as cogeo_version
from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles

IN_MEMORY_THRESHOLD = int(os.environ.get("IN_MEMORY_THRESHOLD", 10980 * 10980))


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


class NodataParamType(click.ParamType):
    """Nodata inddex type."""

    name = "nodata"

    def convert(self, value, param, ctx):
        """Validate and parse band index."""
        try:
            if value.lower() == "nan":
                return numpy.nan
            elif value.lower() in ["nil", "none", "nada"]:
                return None
            else:
                return float(value)
        except (TypeError, ValueError):
            raise click.ClickException("{} is not a valid nodata value.".format(value))


@click.group(short_help="Create and Validate COGEO")
@click.version_option(version=cogeo_version, message="%(version)s")
def cogeo():
    """Rasterio cogeo subcommands."""
    pass


@cogeo.command(short_help="Create COGEO")
@options.file_in_arg
@options.file_out_arg
@click.option("--bidx", "-b", type=BdxParamType(), help="Band indexes to copy.")
@click.option(
    "--cog-profile",
    "-p",
    "cogeo_profile",
    type=click.Choice(cog_profiles.keys()),
    default="deflate",
    help="CloudOptimized GeoTIFF profile (default: deflate).",
)
@click.option(
    "--nodata",
    type=NodataParamType(),
    metavar="NUMBER|nan",
    help="Set nodata masking values for input dataset.",
)
@click.option(
    "--add-mask",
    is_flag=True,
    help="Force output dataset creation with an internal mask (convert alpha "
    "band or nodata to mask).",
)
@click.option(
    "--overview-level",
    type=int,
    help="Overview level (if not provided, appropriate overview level will be "
    "selected until the smallest overview is smaller than the value of the "
    "internal blocksize)",
)
@click.option(
    "--overview-resampling",
    help="Overview creation resampling algorithm.",
    type=click.Choice(
        [it.name for it in ResamplingEnums if it.value in [0, 1, 2, 3, 4, 5, 6, 7]]
    ),
    default="nearest",
)
@click.option(
    "--overview-blocksize",
    default=lambda: os.environ.get("GDAL_TIFF_OVR_BLOCKSIZE", 128),
    help="Overview's internal tile size (default defined by "
    "GDAL_TIFF_OVR_BLOCKSIZE env or 128)",
)
@click.option(
    "--web-optimized", "-w", is_flag=True, help="Create COGEO optimized for Web."
)
@click.option(
    "--latitude-adjustment/--global-maxzoom",
    default=None,
    help="Use dataset native mercator resolution for MAX_ZOOM calculation "
    "(linked to dataset center latitude, default) or ensure MAX_ZOOM equality for multiple "
    "dataset accross latitudes.",
)
@click.option(
    "--resampling",
    "-r",
    help="Resampling algorithm.",
    type=click.Choice(
        [it.name for it in ResamplingEnums if it.value in [0, 1, 2, 3, 4, 5, 6, 7]]
    ),
    default="nearest",
)
@click.option(
    "--in-memory/--no-in-memory",
    default=None,
    help="Force processing raster in memory / not in memory (default: process in memory "
    "if smaller than {:.0f} million pixels)".format(IN_MEMORY_THRESHOLD // 1e6),
)
@click.option("--threads", type=int, default=8)
@options.creation_options
@click.option(
    "--quiet", "-q", help="Remove progressbar and other non-error output.", is_flag=True
)
def create(
    input,
    output,
    bidx,
    cogeo_profile,
    nodata,
    add_mask,
    overview_level,
    overview_resampling,
    overview_blocksize,
    web_optimized,
    latitude_adjustment,
    resampling,
    in_memory,
    threads,
    creation_options,
    quiet,
):
    """Create Cloud Optimized Geotiff."""
    if latitude_adjustment is not None and not web_optimized:
        warnings.warn(
            "'latitude_adjustment' option has to be used with --web-optimized options. "
            "Will be ignored."
        )

    output_profile = cog_profiles.get(cogeo_profile)
    output_profile.update(dict(BIGTIFF=os.environ.get("BIGTIFF", "IF_SAFER")))
    if creation_options:
        output_profile.update(creation_options)

    config = dict(
        NUM_THREADS=threads,
        GDAL_TIFF_INTERNAL_MASK=os.environ.get("GDAL_TIFF_INTERNAL_MASK", True),
        GDAL_TIFF_OVR_BLOCKSIZE=str(overview_blocksize),
    )

    cog_translate(
        input,
        output,
        output_profile,
        bidx,
        nodata,
        add_mask,
        overview_level,
        overview_resampling,
        web_optimized,
        latitude_adjustment,
        resampling,
        in_memory,
        config,
        quiet,
    )


@cogeo.command(short_help="Validate COGEO")
@options.file_in_arg
def validate(input):
    """Validate Cloud Optimized Geotiff."""
    if cog_validate(input):
        click.echo("{} is a valid cloud optimized GeoTIFF".format(input))
    else:
        click.echo("{} is NOT a valid cloud optimized GeoTIFF".format(input))
