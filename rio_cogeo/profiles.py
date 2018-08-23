"""rio_cogeo.profiles: CloudOptimized profiles."""

from rasterio.profiles import Profile


class YCbCrProfile(Profile):
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
                "ycbcr": YCbCrProfile(),
                "webp": WEBPProfile(),
                "zstd": ZSTDProfile(),
                "lzw": LZWProfile(),
                "deflate": DEFLATEProfile(),
                "packbits": PACKBITSProfile(),
                "raw": RAWProfile(),
            }
        )

    def get(self, key):
        """Like normal item access but error."""
        if key not in (self.keys()):
            raise KeyError("{} is not a valid COG profile name".format(key))

        return self[key].copy()


cog_profiles = COGProfiles()
