"""rio_cogeo.profiles: CloudOptimized profiles."""

import warnings

from rasterio.profiles import Profile


class JPEGProfile(Profile):
    """Tiled, pixel-interleaved, JPEG-compressed, YCbCr colorspace, 8-bit GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "JPEG",
        "photometric": "YCbCr",
    }


class WEBPProfile(Profile):
    """Tiled, pixel-interleaved, WEBP-compressed, 8-bit GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "WEBP",
    }


class ZSTDProfile(Profile):
    """Tiled, pixel-interleaved, ZSTD-compressed GTiff.

    Note: ZSTD compression is available since gdal 2.3
    """

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "ZSTD",
    }


class LZWProfile(Profile):
    """Tiled, pixel-interleaved, LZW-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "LZW",
    }


class DEFLATEProfile(Profile):
    """Tiled, pixel-interleaved, DEFLATE-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "DEFLATE",
    }


class PACKBITSProfile(Profile):
    """Tiled, pixel-interleaved, PACKBITS-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "PACKBITS",
    }


class LZMAProfile(Profile):
    """Tiled, pixel-interleaved, LZMA-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "LZMA",
    }


class LERCProfile(Profile):
    """Tiled, pixel-interleaved, LERC-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "LERC",
    }


class LERCDEFLATEProfile(Profile):
    """Tiled, pixel-interleaved, LERC_DEFLATE-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "LERC_DEFLATE",
    }


class LERCZSTDProfile(Profile):
    """Tiled, pixel-interleaved, LERC_ZSTD-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "LERC_ZSTD",
    }


class RAWProfile(Profile):
    """Tiled, pixel-interleaved, no-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
    }


class COGProfiles(dict):
    """CloudOptimized GeoTIFF profiles."""

    def __init__(self):
        """Initialize COGProfiles dict."""
        self.update(
            {
                "jpeg": JPEGProfile(),
                "webp": WEBPProfile(),
                "zstd": ZSTDProfile(),
                "lzw": LZWProfile(),
                "deflate": DEFLATEProfile(),
                "packbits": PACKBITSProfile(),
                "lzma": LZMAProfile(),
                "lerc": LERCProfile(),
                "lerc_deflate": LERCDEFLATEProfile(),
                "lerc_zstd": LERCZSTDProfile(),
                "raw": RAWProfile(),
            }
        )

    def get(self, key):
        """Like normal item access but error."""
        key = key.lower()
        if key not in (self.keys()):
            raise KeyError("{} is not a valid COG profile name".format(key))

        if key in ["zstd", "webp", "lerc", "lerc_deflate", "lerc_zstd"]:
            warnings.warn(
                "Non-standard compression schema: {}. The output COG might not be fully"
                " supported by software not build against latest libtiff.".format(key)
            )

        return self[key].copy()


cog_profiles = COGProfiles()
